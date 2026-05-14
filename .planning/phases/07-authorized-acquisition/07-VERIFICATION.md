---
phase: 07-authorized-acquisition
status: passed
verified_at: "2026-05-14T21:24:00+08:00"
plans:
  - 07-01
  - 07-02
  - 07-03
requirements_verified:
  - V2-DL-01
  - V2-DL-02
  - V2-DL-03
  - V2-DL-04
  - V2-DL-05
  - LANG-04
automated_checks:
  - "python -m pytest tests/test_acquisition.py tests/test_assets.py tests/test_cli.py tests/test_config.py tests/test_skeleton.py tests/test_templates.py -q"
  - "python -m pytest -q"
  - "python -m rsa_cli.cli --root . eval compare"
---

# Phase 7 Verification: Authorized Acquisition

## Verdict

PASSED.

Phase 7 实现了受控的授权全文获取工作流：系统可以从正式 `metadata/P###.yaml` 生成候选来源、记录匹配证据和授权模式，默认通过 `rsa source find P###` 自动审查并下载规则允许的 PDF，同时保留 `--no-download`、候选查看、状态查看和显式下载命令供用户监控与调整。

## Requirement Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `V2-DL-01` | passed | `discover_source_candidates`、`find_sources`、`source_candidates/P###.yaml` 支持 DOI、official URL、arXiv 和 custom provider 候选。 |
| `V2-DL-02` | passed | `download_candidate` / `download_direct_url` 要求明确 `authorization_mode`、`access_mode`、中文授权依据或使用限制，并对 unknown/blocked/title_only fail closed。 |
| `V2-DL-03` | passed | `rsa source find P001` 默认 monitored automation，自动生成候选并下载 approved PDF。 |
| `V2-DL-04` | passed | `--no-download`、`rsa source candidates`、`rsa source status`、`rsa source download --best/--candidate/--url` 提供监控和调整入口。 |
| `V2-DL-05` | passed | 候选记录和 source ledger 保存 match evidence、authorization/access mode、中文原因、local path、sha256、duplicate/failed/downloaded 状态。 |
| `LANG-04` | passed | 新增 CLI help、错误、模板、README、AGENTS 和测试均覆盖中文用户可见内容。 |

## Must-Haves Verification

- `D-01`-`D-11`: 候选发现、provider schema、检索优先级、匹配证据、title-only 阻断已实现。
- `D-12`-`D-17`: 中等授权判定、订阅/授权访问记录、禁止 Sci-Hub/绕过访问控制已实现。
- `D-18`-`D-21`: `find`/`download` 概念分离，默认 monitored_auto，保留人工监控和显式 URL 下载入口。
- `D-22`-`D-28`: PDF 路径、`.tmp`、PDF 校验、`sha256` 去重、多版本和主版本选择已实现。
- `D-29`-`D-30`: 用户可见内容中文优先，英文 schema/flag/key 保持稳定并有中文解释。

## Automated Checks

- `python -m pytest tests/test_acquisition.py tests/test_assets.py tests/test_cli.py tests/test_config.py tests/test_skeleton.py tests/test_templates.py -q`
  - Result: `56 passed`
- `python -m pytest -q`
  - Result: `117 passed`
- `python -m rsa_cli.cli --root . eval compare`
  - Result: 回归数 `0`

## Residual Risk

- v1 下载实现使用直接 URL / `file://` / `urllib` 路径，不包含浏览器会话复用或数据库专用 API connector。
- 复杂机构数据库登录、SSO 和手动 cookie/session 复用仍未实现；这是刻意保留的授权边界，不阻塞 Phase 7。
- 后续 Phase 8 自动阅读必须继续只读取本地、用户提供或已授权 PDF，不得把候选记录直接当成正式学术结论。

## Conclusion

Phase 7 达成目标，可以进入 Phase 8 Auto Reading Draft。
