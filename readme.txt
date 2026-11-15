人工智能开放场景需求撮合与试点治理平台

运行验收：
python3 -m scene_exchange run --fixture fixtures/acceptance.json --database /tmp/scene_exchange.sqlite3 --output /tmp/scene_exchange-output

核验：
python3 -m scene_exchange verify --database /tmp/scene_exchange.sqlite3 --output /tmp/scene_exchange-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.intake.test_demand_contract -v

构建检查：
python3 -m compileall -q scene_exchange tests
