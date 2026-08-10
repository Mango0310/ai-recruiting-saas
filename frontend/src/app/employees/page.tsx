"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getEmployees, getEmployeeStats, createEmployee } from "@/lib/api";

export default function EmployeeList() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const [alertFilter, setAlertFilter] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newEmp, setNewEmp] = useState({
    name: "", position: "", department: "", salary: "",
    hire_date: new Date().toISOString().slice(0, 10), probation_months: 3,
    phone: "", email: "", id_number: "",
    social_insurance: "pending", social_insurance_account: "",
    housing_fund: "pending", housing_fund_account: "",
    bank_name: "", bank_account: "",
    education_degree: "", education_school: "", education_major: "", education_graduation_year: 0,
    emergency_contact_name: "", emergency_contact_phone: "", emergency_contact_relation: "",
    contract_type: "fulltime",
  });

  const fetch = async () => {
    setLoading(true);
    try {
      const [emps, s] = await Promise.all([
        getEmployees(statusFilter || undefined, alertFilter || undefined),
        getEmployeeStats(),
      ]);
      setEmployees(emps);
      setStats(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [statusFilter, alertFilter]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">在职员工台账</h1>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "在职总数", value: stats.total || 0, color: "blue", status: "", alert: "" },
          { label: "试用期", value: stats.probation || 0, color: "yellow", status: "probation", alert: "" },
          { label: "已转正", value: stats.regular || 0, color: "green", status: "regular", alert: "" },
          { label: "转正预警", value: stats.urgent_alerts || 0, color: "red", status: "", alert: "pending" },
          { label: "即将到期", value: stats.upcoming_alerts || 0, color: "orange", status: "", alert: "upcoming" },
        ].map(s => (
          <button
            key={s.label}
            onClick={() => { setStatusFilter(s.status); setAlertFilter(s.alert); }}
            className={`bg-white rounded-lg border p-3 text-left w-full transition hover:border-blue-300 hover:shadow-sm ${s.value > 0 && s.color === "red" ? "border-red-300 bg-red-50" : "border-gray-200"}`}
          >
            <p className={`text-xl font-bold ${s.color === "red" ? "text-red-600" : s.color === "orange" ? "text-orange-600" : "text-blue-600"}`}>
              {s.value}
            </p>
            <p className="text-xs text-gray-500">{s.label}</p>
          </button>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">全部</option>
          <option value="probation">试用期</option>
          <option value="regular">已转正</option>
          <option value="resigned">已离职</option>
        </select>
        <button onClick={fetch} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">刷新</button>
        <button onClick={() => setShowAdd(true)} className="px-4 py-2 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50">
          手动添加员工
        </button>
      </div>

      {loading && <p className="text-gray-400 text-center py-10">加载中...</p>}

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">姓名</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">岗位/部门</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">手机号</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">入职</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">转正</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">学历</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">银行卡</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">状态</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">预警</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">登记</th>
              <th className="text-left px-3 py-3 font-medium text-gray-500 text-xs">操作</th>
            </tr>
          </thead>
          <tbody>
            {!loading && employees.length === 0 && (
              <tr><td colSpan={11} className="py-10 text-center text-gray-400">暂无入职员工</td></tr>
            )}
            {employees.map(e => {
              return (
                <tr key={e.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2">
                    <Link href={`/employees/${e.id}`} className="text-blue-600 hover:underline text-sm font-medium">{e.name}</Link>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600">
                    {e.position}<br /><span className="text-gray-400">{e.department || "—"}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600 font-mono">{e.phone || "—"}</td>
                  <td className="px-3 py-2 text-xs text-gray-600">{e.hire_date}</td>
                  <td className="px-3 py-2 text-xs text-gray-600">
                    {e.probation_end_date}
                    {e.days_until_probation_end != null && e.status === "probation" && (
                      <span className="text-gray-400 ml-1">({e.days_until_probation_end}d)</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600">
                    {e.education_degree ? `${e.education_degree} ${e.education_school || ''}`.substring(0, 12) : "—"}
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600">{e.bank_name || "—"}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      e.status === "probation" ? "bg-yellow-50 text-yellow-700"
                      : e.status === "regular" ? "bg-green-50 text-green-700"
                      : "bg-gray-50 text-gray-600"
                    }`}>
                      {e.status === "probation" ? "试用期" : e.status === "regular" ? "已转正" : e.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {e.probation_alert === "overdue" && <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700">⚠ 已逾期</span>}
                    {e.probation_alert === "urgent" && <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700">⚠ 7天内</span>}
                    {e.probation_alert === "upcoming" && <span className="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-700">14天内</span>}
                    {!e.probation_alert && <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-3 py-2">
                    {e.onboard_completed === "Y" ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">已填写</span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-50 text-gray-500">待填写</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <Link href={`/employees/${e.id}`} className="text-xs text-blue-600 hover:underline">
                      编辑
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Manual Add Employee Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-50 overflow-y-auto py-8" onClick={() => setShowAdd(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">手动添加员工</h2>
              <button onClick={() => setShowAdd(false)} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>
            <p className="text-xs text-gray-500">适用于系统使用前已入职的员工，HR可填写完整个人信息建档</p>

            {/* 基本信息 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">基本信息</p>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">姓名 *</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.name}
                    onChange={e => setNewEmp({...newEmp, name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">手机号</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.phone}
                    onChange={e => setNewEmp({...newEmp, phone: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">邮箱</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.email}
                    onChange={e => setNewEmp({...newEmp, email: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">身份证号</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.id_number}
                    onChange={e => setNewEmp({...newEmp, id_number: e.target.value})} />
                </div>
              </div>
            </div>

            {/* 岗位信息 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">岗位信息</p>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">岗位 *</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.position}
                    onChange={e => setNewEmp({...newEmp, position: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">部门</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.department}
                    onChange={e => setNewEmp({...newEmp, department: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">薪资</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.salary}
                    onChange={e => setNewEmp({...newEmp, salary: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">入职日期</label>
                  <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.hire_date}
                    onChange={e => setNewEmp({...newEmp, hire_date: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">试用期(月)</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.probation_months}
                    onChange={e => setNewEmp({...newEmp, probation_months: parseInt(e.target.value)})}>
                    <option value={1}>1个月</option><option value={2}>2个月</option>
                    <option value={3}>3个月</option><option value={6}>6个月</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">合同类型</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.contract_type}
                    onChange={e => setNewEmp({...newEmp, contract_type: e.target.value})}>
                    <option value="fulltime">全职</option><option value="parttime">兼职</option><option value="intern">实习</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 学历信息 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">学历信息</p>
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">最高学历</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.education_degree}
                    onChange={e => setNewEmp({...newEmp, education_degree: e.target.value})}>
                    <option value="">请选择</option>
                    <option value="博士">博士</option><option value="硕士">硕士</option>
                    <option value="本科">本科</option><option value="大专">大专</option><option value="其他">其他</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">毕业院校</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.education_school}
                    onChange={e => setNewEmp({...newEmp, education_school: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">专业</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.education_major}
                    onChange={e => setNewEmp({...newEmp, education_major: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">毕业年份</label>
                  <input type="number" className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.education_graduation_year || ""}
                    onChange={e => setNewEmp({...newEmp, education_graduation_year: parseInt(e.target.value) || 0})} />
                </div>
              </div>
            </div>

            {/* 社保公积金 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">社保公积金</p>
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">社保</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.social_insurance}
                    onChange={e => setNewEmp({...newEmp, social_insurance: e.target.value})}>
                    <option value="pending">待办理</option><option value="active">已缴纳</option><option value="exempt">不适用</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">社保账号</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.social_insurance_account}
                    onChange={e => setNewEmp({...newEmp, social_insurance_account: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">公积金</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.housing_fund}
                    onChange={e => setNewEmp({...newEmp, housing_fund: e.target.value})}>
                    <option value="pending">待办理</option><option value="active">已缴纳</option><option value="exempt">不适用</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">公积金账号</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.housing_fund_account}
                    onChange={e => setNewEmp({...newEmp, housing_fund_account: e.target.value})} />
                </div>
              </div>
            </div>

            {/* 银行卡 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">银行卡</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">开户行</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.bank_name}
                    onChange={e => setNewEmp({...newEmp, bank_name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">卡号</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.bank_account}
                    onChange={e => setNewEmp({...newEmp, bank_account: e.target.value})} />
                </div>
              </div>
            </div>

            {/* 紧急联系人 */}
            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-400 mb-2">紧急联系人</p>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">姓名</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.emergency_contact_name}
                    onChange={e => setNewEmp({...newEmp, emergency_contact_name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">关系</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.emergency_contact_relation}
                    onChange={e => setNewEmp({...newEmp, emergency_contact_relation: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">电话</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={newEmp.emergency_contact_phone}
                    onChange={e => setNewEmp({...newEmp, emergency_contact_phone: e.target.value})} />
                </div>
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-2">
              <button onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">取消</button>
              <button onClick={async () => {
                if (!newEmp.name || !newEmp.position) return alert("姓名和岗位必填");
                await createEmployee(newEmp);
                setShowAdd(false);
                setNewEmp({
                  name: "", position: "", department: "", salary: "",
                  hire_date: new Date().toISOString().slice(0, 10), probation_months: 3,
                  phone: "", email: "", id_number: "",
                  social_insurance: "pending", social_insurance_account: "",
                  housing_fund: "pending", housing_fund_account: "",
                  bank_name: "", bank_account: "",
                  education_degree: "", education_school: "", education_major: "", education_graduation_year: 0,
                  emergency_contact_name: "", emergency_contact_phone: "", emergency_contact_relation: "",
                  contract_type: "fulltime",
                });
                fetch();
              }} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">添加员工</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
