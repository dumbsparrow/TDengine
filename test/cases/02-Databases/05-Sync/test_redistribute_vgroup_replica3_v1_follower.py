import time
from new_test_framework.utils import tdLog, tdSql, sc, clusterComCheck, clusterComCheck


class TestRedistributeVgroupReplica3V1Follower:

    def setup_class(cls):
        tdLog.debug(f"start to execute {__file__}")

    def test_redistribute_vgroup_replica3_v1_follower(self):
        """redistribute vgroup replica3 v1 follower

        1. -

        Catalog:
            - Database:Sync

        Since: v3.0.0.0

        Labels: common,ci

        Jira: None

        History:
            - 2025-5-6 Simon Guan Migrated from tsim/dnode/redistribute_vgroup_replica3_v1_follower.sim

        """

        clusterComCheck.checkDnodes(5)
        tdSql.execute(f"alter dnode 1 'supportVnodes' '0'")
        clusterComCheck.checkDnodeSupportVnodes(1, 0)

        sc.dnodeStop(5)
        clusterComCheck.checkDnodes(4)

        tdSql.execute(f"create user u1 pass 'taosdata'")

        tdLog.info(f"=============== step1 create dnode2")
        tdSql.query(f"select * from information_schema.ins_dnodes")
        tdSql.checkRows(5)
        tdSql.checkKeyData(1, 4, "ready")
        tdSql.checkKeyData(2, 4, "ready")
        tdSql.checkKeyData(3, 4, "ready")
        tdSql.checkKeyData(4, 4, "ready")
        tdSql.checkKeyData(4, 4, "offline")

        tdLog.info(f"=============== step2: create db")
        tdSql.execute(f"create database d1 vgroups 1 replica 3")
        clusterComCheck.checkDbReady("d1")

        # dnode not exist
        tdSql.error(f"redistribute vgroup 3 dnode 6 dnode 3 dnode 4")
        # vgroup not exist
        tdSql.error(f"redistribute vgroup 3 dnode 5 dnode 3 dnode 4")
        # un changed
        # sql_error redistribute vgroup 2 dnode 2 dnode 3 dnode 4
        # no enought vnodes
        tdSql.error(f"redistribute vgroup 2 dnode 1 dnode 3 dnode 4")
        # offline vnodes
        tdSql.error(f"redistribute vgroup 2 dnode 5 dnode 3 dnode 4")
        # Invalid replica
        tdSql.error(f"redistribute vgroup 2 dnode 5")
        tdSql.error(f"redistribute vgroup 2 dnode 5 dnode 3")
        tdSql.error(f"redistribute vgroup 2 dnode 2 dnode 3")
        tdSql.error(f"redistribute vgroup 2 dnode 2 dnode 2")
        tdSql.error(f"redistribute vgroup 3 dnode 2 dnode 2")
        tdSql.error(f"redistribute vgroup 2 dnode 2 dnode 2 dnode 3")

        sc.dnodeStart(5)
        clusterComCheck.checkDnodes(5)

        tdSql.query(f"select * from information_schema.ins_dnodes")
        tdSql.checkRows(5)
        tdSql.checkKeyData(1, 4, "ready")
        tdSql.checkKeyData(2, 4, "ready")
        tdSql.checkKeyData(3, 4, "ready")
        tdSql.checkKeyData(4, 4, "ready")
        tdSql.checkKeyData(5, 4, "ready")

        tdLog.info(f"=============== step3: create database")
        leaderExist = 0
        leaderVnode = 0
        follower1 = 0
        follower2 = 0

        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )
        tdSql.checkRows(1)

        if tdSql.getData(0, 4) == "leader":
            leaderExist = 1
            leaderVnode = 2
            follower1 = 3
            follower2 = 4

        if tdSql.getData(0, 7) == "leader":
            leaderExist = 1
            leaderVnode = 3
            follower1 = 2
            follower2 = 4

        if tdSql.getData(0, 10) == "leader":
            leaderExist = 1
            leaderVnode = 4
            follower1 = 2
            follower2 = 3

        tdLog.info(f"leader {leaderVnode}")
        tdLog.info(f"follower1 {follower1}")
        tdLog.info(f"follower2 {follower2}")

        tdSql.execute(f"use d1")
        tdSql.execute(f"create table d1.st (ts timestamp, i int) tags (j int)")
        tdSql.execute(f"create table d1.c1 using st tags(1)")
        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step31:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower2} dnode 5"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower2} dnode 5"
        )

        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step32:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode 5"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode 5"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step33:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower2}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower2}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step34:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower1}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower1}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step34:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower2} dnode {follower1}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower2} dnode {follower1}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step36:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode 5"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode 5"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step37:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower2}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower2}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step38:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower1}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode 5 dnode {follower1}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)

        tdLog.info(f"=============== step39:")
        tdLog.info(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode {follower2}"
        )
        tdSql.execute(
            f"redistribute vgroup 2 dnode {leaderVnode} dnode {follower1} dnode {follower2}"
        )
        tdSql.query(f"show d1.vgroups")
        tdLog.info(
            f"===> {tdSql.getData(0,0)} {tdSql.getData(0,1)} {tdSql.getData(0,2)} {tdSql.getData(0,3)} {tdSql.getData(0,4)} {tdSql.getData(0,5)} {tdSql.getData(0,6)} {tdSql.getData(0,7)} {tdSql.getData(0,8)} {tdSql.getData(0,9)}"
        )

        tdSql.query(f"show d1.tables")
        tdSql.checkRows(1)
