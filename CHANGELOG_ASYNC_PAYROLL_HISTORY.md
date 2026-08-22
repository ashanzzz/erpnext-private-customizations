# Payroll Async Recalculation & History Audit Upgrade

Date: 2026-08-21

## Business model

- The Qifu payroll workbench is organized into seven explicit business tabs:
  1. 员工薪酬档案（母表底册）
  2. 外部实发与发放表（24列）
  3. 社会保险台账与配置
  4. 住房公积金台账与配置
  5. 个人所得税申报台账
  6. 月度薪酬综合结算
  7. 历史数据
- Tabs 1/2/3/4/7 are authoritative input or controlled-correction surfaces. Saving an input marks the affected employee/month dirty and submits a server-side recalculation task.
- Tabs 5/6 are calculation/result surfaces. The old dedicated “重新核定当月个税” and “重新融合核算” UI actions are no longer used in the Qifu workbench.
- Tax participation rule: 临时工/零工 do not enter the IIT ledger; 返聘工/退休返聘/其他-返聘工 continue to participate in cumulative withholding.

## Asynchronous calculation center

- Added `Ashan Payroll Recalculation Task` as an auditable server-generated task record.
- Recalculation runs through Frappe background jobs (`long` queue, enqueue after commit).
- Tasks are coalesced to avoid duplicate queued work; overlapping whole-month ranges are merged and superseded queued employee tasks are cancelled.
- Payroll writes are serialized by company with a Redis lock to avoid concurrent parent-document overwrite races.
- Calculation status is projected to the affected monthly payroll rows: 待计算 / 排队中 / 计算中 / 已计算 / 已跳过 / 计算失败.
- The workbench displays requested/start/completed time, trigger source, engine version, task ID and failure detail, with manual retry and force-recalculate options.
- Input hashes skip unchanged employee calculations unless force-recompute is explicitly requested.

## Cumulative IIT integrity

- The verified VBA-aligned `derive_gross_from_net_vba()` remains the tax-after reverse-calculation core.
- Historical corrections cascade forward because cumulative withholding depends on earlier months.
- If an earlier month fails, later months in the same cumulative chain are not calculated from stale history; they are marked failed with the failed prerequisite month.
- A one-month history correction preserves the corrected saved snapshot instead of immediately refreshing it back from the current employee master.
- Historical months in a multi-month correction keep their period snapshots; only the final current-period month refreshes current master inputs.

## History data

- Tab 7 retains a compact cumulative summary and adds “完整核算 · 68列+审计”.
- The complete view uses the same 68 calculation columns as the VBA-aligned IIT ledger, plus ERP audit metadata.
- Frozen months are read-only financial snapshots.
- Unlocked historical input correction is restricted to authoritative salary-side input, personal SS/HF paid amounts and seven special additional deductions; calculated tax outputs cannot be edited directly.

## Final lock integrity

- Final monthly lock now performs a server-side asynchronous-calculation readiness check.
- A month cannot be finally locked while any payroll row is pending, queued, running, failed or uncomputed, or while an overlapping calculation task is active.
- Existing payroll proof period/amount validation is still re-run at final lock time.

## Additional hardening / bug fixes

- Fixed period roster logic so future joiners are excluded and employees who left later are retained in the correct historical months.
- Locked SS/HF views use monthly snapshot values rather than today's employee master/configuration.
- Removed person-specific contribution exceptions; rules are data/employee-type driven.
- Sensitive payroll write RPCs use POST and permission checks; legacy payroll UI write calls were aligned to POST.
- Server-generated recalculation task records are read-only to business roles; task history cannot be manually fabricated through the DocType form.
- Removed real employee/payroll seed files and live HTML/boot dumps from the Git-ready source; only example seed structures remain.

## Deployment

```bash
bench --site <site> migrate
bench build --app ashan_cn_procurement
bench --site <site> clear-cache
bench restart
```

After deployment, run the repository's live Frappe/Playwright acceptance workflow in the target ERPNext 16 environment. The packaged source is statically validated, but no live site/container is bundled into this ZIP.
