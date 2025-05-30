import time
from new_test_framework.utils import tdLog, tdSql, sc, clusterComCheck, clusterComCheck


class TestStableDnode2Stop:

    def setup_class(cls):
        tdLog.debug(f"start to execute {__file__}")

    def test_stable_dnode2_stop(self):
        """stable dnode2 stop

        1. -

        Catalog:
            - DataBase:Sync

        Since: v3.0.0.0

        Labels: common,ci

        Jira: None

        History:
            - 2025-5-5 Simon Guan Migrated from tsim/vnode/stable_dnode2_stop.sim

        """

        clusterComCheck.checkDnodes(2)
        tdSql.execute(f"alter dnode 1 'supportVnodes' '4'")
        tdSql.execute(f"alter dnode 2 'supportVnodes' '4'")

        clusterComCheck.checkDnodeSupportVnodes(1, 4)
        clusterComCheck.checkDnodeSupportVnodes(2, 4)

        clusterComCheck.checkDnodes(2)

        tdLog.info(f"========== step1")

        tdLog.info(f"======================== dnode1 start")

        dbPrefix = "d2s_db"
        tbPrefix = "d2s_tb"
        mtPrefix = "d2s_mt"
        tbNum = 10
        rowNum = 20
        totalNum = 200

        tdSql.query(f"select * from information_schema.ins_dnodes;")
        tdLog.info(f"dnodes ==> {tdSql.getRows()})")
        tdSql.checkRows(2)

        tdLog.info(f"=============== step1")
        i = 0
        db = dbPrefix + str(i)
        mt = mtPrefix + str(i)

        tdSql.execute(f"create database {db} vgroups 3")
        tdSql.execute(f"use {db}")
        tdSql.execute(f"create table {mt} (ts timestamp, tbcol int) TAGS(tgcol int)")

        i = 0
        while i < tbNum:
            tb = tbPrefix + str(i)
            tdSql.execute(f"create table {tb} using {mt} tags( {i} )")

            x = 0
            while x < rowNum:
                val = x * 60000
                ms = 1519833600000 + val
                tdSql.execute(f"insert into {tb} values ({ms} , {x} )")
                x = x + 1

            i = i + 1

        tdSql.query(f"show vgroups")
        tdLog.info(f"vgroups ==> {tdSql.getRows()})")
        tdSql.checkRows(3)

        sc.dnodeStop(2)
        clusterComCheck.checkDnodes(1)

        tdLog.info(f"=============== step2")
        tdSql.error(f"select count(*) from {mt}")
        tdSql.error(f"select count(tbcol) from {mt}")

        sc.dnodeStart(2)
        clusterComCheck.checkDnodes(2)

        tdSql.query(f"select * from information_schema.ins_dnodes")
        tdSql.checkRows(2)
        tdSql.checkKeyData(1, 4, "ready")
        tdSql.checkKeyData(2, 4, "ready")

        tdLog.info(f"=============== step3")
        tdSql.query(f"select count(tbcol) as c from {mt} where ts <= 1519833840000")
        tdLog.info(f"===> {tdSql.getData(0,0)}")
        tdSql.checkData(0, 0, 50)

        tdSql.query(f"select count(tbcol) as c from {mt} where tgcol < 5")
        tdLog.info(f"===> {tdSql.getData(0,0)}")
        tdSql.checkData(0, 0, 100)

        tdSql.query(
            f"select count(tbcol) as c from {mt} where tgcol < 5 and ts <= 1519833840000"
        )
        tdLog.info(f"===> {tdSql.getData(0,0)}")
        tdSql.checkData(0, 0, 25)

        tdLog.info(f"=============== step4")
        tdSql.query(f"select _wstart, count(tbcol) as b from {mt} interval(1m)")
        tdLog.info(f"===> {tdSql.getData(0,1)}")
        tdSql.checkData(0, 1, 10)

        tdSql.query(f"select _wstart, count(tbcol) as b from {mt} interval(1d)")
        tdLog.info(f"===> {tdSql.getData(0,1)}")
        tdSql.checkData(0, 1, 200)

        tdLog.info(f"=============== step5")
        tdSql.query(f"select count(tbcol) as b from {mt} group by tgcol")
        tdLog.info(f"===> {tdSql.getData(0,0)}")
        tdSql.checkData(0, 0, rowNum)
        tdSql.checkRows(tbNum)

        tdLog.info(f"=============== clear")
        tdSql.execute(f"drop database {db}")
        tdSql.query(f"select * from information_schema.ins_databases")
        tdSql.checkRows(2)
