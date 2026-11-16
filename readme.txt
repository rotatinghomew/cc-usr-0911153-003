人工智能开放场景需求撮合与试点治理平台

试点基础容量：Application.register_supplier 登记供应商与当前可占用的并行试点名额，
accept_pilot 将已登记需求占用一个名额；finish_pilot 记录完成或退出，释放当前名额，
历史试点结果保留。capacity_status 可查询余额及已接受试点。事务内检查余额并接受试点，
避免两个试点竞争一个席位时超额确认。

供给可靠性分析：supply_analysis / supplier_analysis 依据已履约（completed）、退出
（withdrawn）和尚未成熟（active）的试点记录，给出供应商可支持的承诺区间。承诺上限
只由已关闭试点证据决定：不足 min_evidence 次关闭试点时仅按 probation_slots 试运行，
退出计入失败且降低上限；match_score 与 expected_benefit 单独报告，不抬高承诺上限。
收益同时报告预期均值与已实现区间（退出按 0 计，未上报完成不计入但注明）。

确认占用容量：accept_pilot 在事务内占用实际 units，并按包含本单在内的组合重新判断
可执行性；承诺区间在复核后发生变化时需重新分析，可用 reviewed_fingerprint 强制校验。
超过推荐值但不超过证据上限须由 approver + reason 审批；超过上限一律拒绝。
commitment_trail 记录每次建议值、申请值、最终占用与差异；supplier_revise 变更承诺
名额并留痕。关闭后的容量可供后续试点复用，原试点结果保持不变。

供给与试点命令：
python3 -m scene_exchange supply --database <db> [--supplier <id>]
python3 -m scene_exchange pilot-status --database <db> --supplier <id>
python3 -m scene_exchange pilot-accept --database <db> --demand <id> --supplier <id> [--units N]
python3 -m scene_exchange pilot-finish --database <db> --demand <id> --status completed|withdrawn
python3 -m scene_exchange commitment-trail --database <db> [--demand <id>] [--supplier <id>]
python3 -m scene_exchange supplier-revise --database <db> --supplier <id> --slots N --reason <text>

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
