人工智能开放场景需求撮合与试点治理平台

试点基础容量：Application.register_supplier 登记供应商与当前可占用的并行试点名额，
accept_pilot 将已登记需求占用一个名额；finish_pilot 记录完成或退出，释放当前名额，
历史试点结果保留。capacity_status 可查询余额及已接受试点。事务内检查余额并接受试点，
避免两个试点竞争一个席位时超额确认。当前尚不依据履约样本估计可靠性或做组合收益分析，
也尚不支持按分析建议更新名额；这些是后续业务功能而非现有基线能力。

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
