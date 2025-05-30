/*
 * Copyright (c) 2019 TAOS Data, Inc. <jhtao@taosdata.com>
 *
 * This program is free software: you can use, redistribute, and/or modify
 * it under the terms of the GNU Affero General Public License, version 3
 * or later ("AGPL"), as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#define _DEFAULT_SOURCE
#include "syncCommit.h"
#include "syncIndexMgr.h"
#include "syncRaftLog.h"
#include "syncRaftStore.h"
#include "syncUtil.h"

// \* Leader i advances its commitIndex.
// \* This is done as a separate step from handling AppendEntries responses,
// \* in part to minimize atomic regions, and in part so that leaders of
// \* single-server clusters are able to mark entries committed.
// AdvanceCommitIndex(i) ==
//     /\ state[i] = Leader
//     /\ LET \* The set of servers that agree up through index.
//            Agree(index) == {i} \cup {k \in Server :
//                                          matchIndex[i][k] >= index}
//            \* The maximum indexes for which a quorum agrees
//            agreeIndexes == {index \in 1..Len(log[i]) :
//                                 Agree(index) \in Quorum}
//            \* New value for commitIndex'[i]
//            newCommitIndex ==
//               IF /\ agreeIndexes /= {}
//                  /\ log[i][Max(agreeIndexes)].term = currentTerm[i]
//               THEN
//                   Max(agreeIndexes)
//               ELSE
//                   commitIndex[i]
//        IN commitIndex' = [commitIndex EXCEPT ![i] = newCommitIndex]
//     /\ UNCHANGED <<messages, serverVars, candidateVars, leaderVars, log>>
//

static inline int64_t syncNodeAbs64(int64_t a, int64_t b) {
  int64_t c = a > b ? a - b : b - a;
  return c;
}

int32_t syncNodeDynamicQuorum(const SSyncNode* pSyncNode) { return pSyncNode->quorum; }

bool syncNodeAgreedUpon(SSyncNode* pNode, SyncIndex index) {
  int            count = 0;
  SSyncIndexMgr* pMatches = pNode->pMatchIndex;
  if (pNode->replicaNum != pMatches->replicaNum) {
    terrno = TSDB_CODE_SYN_INTERNAL_ERROR;
    return false;
  };

  for (int i = 0; i < pNode->totalReplicaNum; i++) {
    if(pNode->raftCfg.cfg.nodeInfo[i].nodeRole == TAOS_SYNC_ROLE_VOTER){
      SyncIndex matchIndex = pMatches->index[i];
      if (matchIndex >= index) {
        count++;
      }
    }
  }

  return count >= pNode->quorum;
}

int64_t syncNodeUpdateCommitIndex(SSyncNode* ths, SyncIndex commitIndex) {
  int32_t   code = 0;
  SyncIndex lastVer = ths->pLogStore->syncLogLastIndex(ths->pLogStore);
  commitIndex = TMAX(commitIndex, ths->commitIndex);
  ths->commitIndex = TMIN(commitIndex, lastVer);
  // TODO add return when error
  (void)ths->pLogStore->syncLogUpdateCommitIndex(ths->pLogStore, ths->commitIndex);
  return ths->commitIndex;
}

int64_t syncNodeCheckCommitIndex(SSyncNode* ths, SyncIndex indexLikely, const STraceId *trace) {
  int32_t code = 0;
  if (indexLikely > ths->commitIndex && syncNodeAgreedUpon(ths, indexLikely)) {
    SyncIndex commitIndex = indexLikely;
    SyncIndex returnIndex = syncNodeUpdateCommitIndex(ths, commitIndex);
    sGDebug(trace, "vgId:%d, index:%" PRId64 ", agreed upon, role:%d term:%" PRId64 " return index:%" PRId64, ths->vgId,
            commitIndex, ths->state, raftStoreGetTerm(ths), returnIndex);
  }
  return ths->commitIndex;
}

int64_t syncNodeUpdateAssignedCommitIndex(SSyncNode* ths, SyncIndex assignedCommitIndex) {
  int32_t   code = 0;
  SyncIndex lastVer = ths->pLogStore->syncLogLastIndex(ths->pLogStore);
  assignedCommitIndex = TMAX(assignedCommitIndex, ths->assignedCommitIndex);
  ths->assignedCommitIndex = TMIN(assignedCommitIndex, lastVer);
  // TODO add return when error
  (void)ths->pLogStore->syncLogUpdateCommitIndex(ths->pLogStore, ths->assignedCommitIndex);
  return ths->commitIndex;
}
