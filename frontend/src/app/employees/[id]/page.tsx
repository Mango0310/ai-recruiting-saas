"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getEmployee, updateEmployee, getProbationStatus, generateProbationEvaluation,
         addManagerEvaluation, getFeedbackLoop, regenerateOnboardToken, getEmployeeProfileReport } from "@/lib/api";

const statusLabel: Record<string, string> = { probation: "试用期", regular: "已转正", resigned: "已离职" };
const statusOptions = [{ value: "probation", label: "试用期" },{ value: "regular", label: "已转正" },{ value: "resigned", label: "已离职" }];
const siOptions = [{ value: "pending", label: "待办理" },{ value: "active", label: "已缴纳" },{ value: "exempt", label: "不适用" }];
const contractOptions = [{ value: "fulltime", label: "全职" },{ value: "parttime", label: "兼职" },{ value: "intern", label: "实习" }];

// Radar chart helpers
const dimOrder = ["technical_expertise","business_acumen","execution","collaboration","growth_potential","leadership"];
const dimAngles = [-90,-30,30,90,150,-150];
function rad(a:number){return (a*Math.PI)/180;}
function getHexPoints(cx:number,cy:number,r:number){return dimAngles.map(a=>`${cx+r*Math.cos(rad(a))},${cy+r*Math.sin(rad(a))}`).join(" ");}
function getAxisLines(cx:number,cy:number,r:number){return dimAngles.map(a=>({x1:cx,y1:cy,x2:cx+r*Math.cos(rad(a)),y2:cy+r*Math.sin(rad(a))}));}
function getDataPoints(s:Record<string,{score:number}>,cx:number,cy:number,r:number){return dimOrder.map((k,i)=>{const v=(s[k]?.score||0)/10;return`${cx+r*v*Math.cos(rad(dimAngles[i]))},${cy+r*v*Math.sin(rad(dimAngles[i]))}`;}).join(" ");}
function getScoreDots(s:Record<string,{score:number}>,cx:number,cy:number,r:number){return dimOrder.map((k,i)=>{const v=(s[k]?.score||0)/10;return{x:cx+r*v*Math.cos(rad(dimAngles[i])),y:cy+r*v*Math.sin(rad(dimAngles[i]))};});}

function Field({label,value,editing,children}:{label:string;value?:string;editing:boolean;children?:React.ReactNode}){
  return <div><span className="text-gray-400 text-xs">{label}</span>{editing&&children?children:<p className="font-medium text-sm">{value||"—"}</p>}</div>;
}

const inputCls="w-full border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400";
const selectCls="w-full border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 bg-white";

export default function EmployeeDetail(){
  const {id}=useParams<{id:string}>();
  const [emp,setEmp]=useState<any>(null);
  const [loading,setLoading]=useState(true);
  const [editing,setEditing]=useState(false);
  const [saving,setSaving]=useState(false);
  const [form,setForm]=useState<Record<string,string>>({});
  const [probation,setProbation]=useState<any>(null);
  const [evalLoading,setEvalLoading]=useState(false);
  const [managerNote,setManagerNote]=useState("");
  const [feedbackLoop,setFeedbackLoop]=useState<any>(null);
  const [feedbackLoading,setFeedbackLoading]=useState(false);
  const [regenerating,setRegenerating]=useState(false);
  const [empProfile,setEmpProfile]=useState<any>(null);
  const [profileLoading,setProfileLoading]=useState(false);

  const fi=useParams();
  const fetch=async()=>{setLoading(true);try{setEmp(await getEmployee(Number(fi.id)));}finally{setLoading(false);}};
  const fetchProbation=async()=>{try{setProbation(await getProbationStatus(Number(fi.id)));}catch{}};
  const fetchFeedbackLoop=async()=>{setFeedbackLoading(true);try{setFeedbackLoop(await getFeedbackLoop(Number(fi.id)));}finally{setFeedbackLoading(false);}};
  const fetchEmployeeProfile=async()=>{setProfileLoading(true);try{setEmpProfile(await getEmployeeProfileReport(Number(fi.id)));}finally{setProfileLoading(false);}};

  useEffect(()=>{fetch();fetchProbation();},[fi.id]);

  const startEdit=()=>{if(!emp)return;setForm({id_number:emp.id_number||"",position:emp.position||"",department:emp.department||"",reports_to:emp.reports_to||"",salary:emp.salary||"",contract_type:emp.contract_type||"fulltime",contract_end_date:emp.contract_end_date||"",social_insurance:emp.social_insurance||"pending",social_insurance_account:emp.social_insurance_account||"",housing_fund:emp.housing_fund||"pending",housing_fund_account:emp.housing_fund_account||"",bank_name:emp.bank_name||"",bank_account:emp.bank_account||"",emergency_contact_name:emp.emergency_contact_name||"",emergency_contact_phone:emp.emergency_contact_phone||"",emergency_contact_relation:emp.emergency_contact_relation||"",status:emp.status||"probation",notes:emp.notes||""});setEditing(true);};
  const cancelEdit=()=>{setEditing(false);setSaving(false);};
  const handleSave=async()=>{if(!emp)return;setSaving(true);try{await updateEmployee(emp.id,form);setEditing(false);setSaving(false);await fetch();}catch{alert("保存失败");setSaving(false);}};
  const update=(k:string,v:string)=>setForm({...form,[k]:v});
  const handleGenerateEval=async(n?:string)=>{setEvalLoading(true);try{await generateProbationEvaluation(Number(fi.id),n||undefined);await fetchProbation();}catch(e:any){alert(e?.response?.data?.detail||"生成评估失败");}finally{setEvalLoading(false);}};
  const handleManualEval=async()=>{if(!managerNote.trim())return;setEvalLoading(true);try{await addManagerEvaluation(Number(fi.id),managerNote);setManagerNote("");await fetchProbation();}catch{alert("保存失败");}finally{setEvalLoading(false);}};
  const handleRegenerateToken=async()=>{if(!confirm("确认重新生成入职链接？旧链接将立即失效。"))return;setRegenerating(true);try{await regenerateOnboardToken(Number(fi.id));await fetch();}catch{alert("操作失败");}finally{setRegenerating(false);}};

  if(loading)return<div className="py-20 text-center text-gray-500">加载中...</div>;
  if(!emp)return<div className="py-20 text-center text-red-500">员工不存在</div>;

  return<div className="max-w-4xl mx-auto space-y-6">
    {/* Header */}
    <div className="flex items-center justify-between">
      <div><Link href="/employees" className="text-sm text-gray-400 hover:text-gray-600">&larr; 员工台账</Link><h1 className="text-2xl font-bold mt-1">{emp.name}</h1><p className="text-gray-500 text-sm">{editing?<input className={`${inputCls} mt-1 max-w-xs`} value={form.position} onChange={e=>update("position",e.target.value)}/>:`${emp.position} · ${emp.department} · ${statusLabel[emp.status]||emp.status}`}</p></div>
      <div className="flex items-center gap-2">{editing?<><button onClick={cancelEdit} className="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">取消</button><button onClick={handleSave} disabled={saving} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">{saving?"保存中...":"保存"}</button></>:<><span className={`text-sm px-3 py-1 rounded-full ${emp.status==="probation"?"bg-yellow-50 text-yellow-700 border border-yellow-200":emp.status==="regular"?"bg-green-50 text-green-700 border border-green-200":"bg-gray-50 text-gray-600 border border-gray-200"}`}>{statusLabel[emp.status]||emp.status}</span><button onClick={startEdit} className="ml-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">编辑</button></>}</div>
    </div>

    {/* Alerts */}
    {emp.probation_alert&&<div className={`rounded-lg p-3 text-sm ${emp.probation_alert==="overdue"?"bg-red-50 border border-red-200 text-red-700":emp.probation_alert==="urgent"?"bg-red-50 border border-red-200 text-red-700":"bg-orange-50 border border-orange-200 text-orange-700"}`}>{emp.probation_alert==="overdue"?"试用期已逾期，请尽快处理转正！":emp.probation_alert==="urgent"?`试用期还有 ${emp.days_until_probation_end} 天到期，需在7天内完成转正评估`:`试用期还有 ${emp.days_until_probation_end} 天到期`}</div>}

    {/* ── Capability Profile (first thing you see) ── */}
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-6 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">能力画像</h3>
        {!empProfile?.profile&&<button onClick={fetchEmployeeProfile} disabled={profileLoading} className="text-xs text-blue-600 hover:underline">{profileLoading?"生成中...":"AI 生成画像"}</button>}
      </div>
      {empProfile?.profile&&<div className="p-6 space-y-5">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-bold text-blue-800">综合画像</p>
            <div className="flex gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${empProfile.profile.career_stage==="growth"?"bg-green-100 text-green-700":"bg-blue-100 text-blue-700"}`}>{empProfile.profile.career_stage==="early"?"成长期":empProfile.profile.career_stage==="growth"?"快速发展期":empProfile.profile.career_stage==="mature"?"成熟期":"瓶颈期"}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{empProfile.profile.team_role==="core_contributor"?"核心贡献者":empProfile.profile.team_role==="specialist"?"领域专家":empProfile.profile.team_role==="coordinator"?"协调者":empProfile.profile.team_role==="mentor"?"导师":"潜力领导者"}</span>
            </div>
          </div>
          <p className="text-sm text-blue-700">{empProfile.profile.summary}</p>
        </div>
        {empProfile.profile.scores&&<div className="flex flex-col items-center">
          <div className="relative w-56 h-56">
            <svg viewBox="0 0 200 200" className="w-full h-full">
              {[1,2,3,4,5].map(r=><polygon key={r} points={getHexPoints(100,100,r*18)} fill="none" stroke="#e5e7eb" strokeWidth="1"/>)}
              {getAxisLines(100,100,90).map((l,i)=><line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="#e5e7eb" strokeWidth="0.5"/>)}
              <polygon points={getDataPoints(empProfile.profile.scores,100,100,90)} fill="rgba(59,130,246,0.25)" stroke="#3b82f6" strokeWidth="2"/>
              {getScoreDots(empProfile.profile.scores,100,100,90).map((d,i)=><circle key={i} cx={d.x} cy={d.y} r="4" fill="#3b82f6" stroke="white" strokeWidth="1.5"/>)}
            </svg>
          </div>
          <p className="text-xs text-gray-400 mt-1">能力雷达图（满分10分）</p>
        </div>}
        <div className="grid grid-cols-2 gap-3 text-xs">
          {empProfile.profile.scores&&Object.entries(empProfile.profile.scores as Record<string,any>).map(([k,v]:[string,any])=>{
            const names:Record<string,string>={technical_expertise:"专业能力",business_acumen:"业务理解",execution:"执行力",collaboration:"协作",growth_potential:"成长潜力",leadership:"领导力"};
            return<div key={k} className="flex items-center gap-2"><span className="w-14 text-gray-500">{names[k]||k}</span><div className="flex-1 h-1.5 bg-gray-200 rounded-full"><div className="h-full bg-blue-500 rounded-full" style={{width:`${((v.score||0)/10)*100}%`}}/></div><span className="font-bold text-gray-700 w-4 text-right">{v.score}</span></div>;
          })}
        </div>
        {empProfile.profile.strengths?.length>0&&<div className="border-t pt-3"><p className="text-xs font-medium text-green-600 mb-2">核心优势</p>{empProfile.profile.strengths.map((s:any,i:number)=><div key={i} className="mb-2 pl-3 border-l-2 border-green-200"><p className="text-sm font-medium text-gray-800">{s.point}</p><p className="text-xs text-gray-400">{s.evidence}</p></div>)}</div>}
        {empProfile.profile.growth_areas?.length>0&&<div className="border-t pt-3"><p className="text-xs font-medium text-orange-600 mb-2">待发展领域</p>{empProfile.profile.growth_areas.map((g:any,i:number)=><div key={i} className="mb-2 pl-3 border-l-2 border-orange-200"><p className="text-sm font-medium text-gray-800">{g.point}</p><p className="text-xs text-orange-500">{g.suggestion}</p></div>)}</div>}
        <p className="text-xs text-gray-300 text-right">生成于 {empProfile.profile.generated_at}</p>
      </div>}
      {!empProfile?.profile&&!profileLoading&&<div className="p-6 text-center text-xs text-gray-400">点击"AI 生成画像"综合分析员工能力</div>}
      {profileLoading&&<div className="p-6 text-center"><div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"/><p className="text-xs text-gray-400">AI 正在生成能力画像...</p></div>}
    </div>

    {/* ── Probation Tracking ── */}
    {emp.status==="probation"&&probation&&<div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-6 py-3 bg-gray-50 border-b flex items-center justify-between"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">试用期追踪</h3><span className="text-xs text-gray-400">入职 {probation.days_employed} 天 · 转正日 {probation.probation_end_date}</span></div>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          {probation.milestones?.map((m:any,i:number)=><div key={i} className="flex-1 flex items-center">
            <div className="flex flex-col items-center flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${m.evaluated?"bg-green-500 text-white":m.reached?"bg-blue-500 text-white ring-2 ring-blue-200":"bg-gray-200 text-gray-500"}`}>{m.evaluated?"✓":m.reached?i+1:"·"}</div>
              <p className={`text-xs mt-1 font-medium ${m.is_current?"text-blue-600":m.evaluated?"text-green-600":"text-gray-400"}`}>{m.label}</p><p className="text-xs text-gray-400">第{m.day}天</p>
            </div>
            {i<(probation.milestones?.length||0)-1&&<div className={`h-0.5 flex-1 -mt-4 ${m.evaluated?"bg-green-300":"bg-gray-200"}`}/>}
          </div>)}
        </div>
        {probation.evaluations?.length>0&&<div className="space-y-3 border-t pt-4"><p className="text-xs font-medium text-gray-400">评估记录</p>
          {probation.evaluations.map((e:any,i:number)=>{
            const avgScore=e.scores?Math.round((e.scores.adaption+e.scores.performance+e.scores.collaboration+e.scores.potential)/4*10)/10:0;
            return<div key={i} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${e.generated_by==="ai"?"bg-purple-100 text-purple-700":"bg-blue-100 text-blue-700"}`}>{e.generated_by==="ai"?"AI评估":"主管评估"}</span>
                  <span className="text-sm font-medium">{e.stage}</span>
                </div>
                <div className="flex items-center gap-2"><div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden"><div className={`h-full rounded-full ${avgScore>=4?"bg-green-500":avgScore>=3?"bg-blue-500":avgScore>=2?"bg-yellow-500":"bg-red-500"}`} style={{width:`${(avgScore/5)*100}%`}}/></div><span className="text-xs font-bold text-gray-600">{avgScore}/5</span></div>
              </div>
              {e.scores&&<div className="grid grid-cols-4 gap-2 mb-2 text-xs">{[{key:"adaption",label:"适应"},{key:"performance",label:"产出"},{key:"collaboration",label:"协作"},{key:"potential",label:"潜力"}].map(d=><div key={d.key} className="text-center"><p className="text-lg font-bold text-gray-700">{e.scores[d.key]}</p><p className="text-gray-400">{d.label}</p></div>)}</div>}
              <p className="text-sm text-gray-700">{e.strengths}</p>
              {e.risks&&<p className="text-xs text-orange-600 mt-1">⚠ {e.risks}</p>}
              <div className="flex items-center justify-between mt-2"><span className={`text-xs px-2 py-0.5 rounded-full ${e.recommendation?.includes("转正")?"bg-green-50 text-green-700":e.recommendation?.includes("延长")?"bg-red-50 text-red-700":"bg-blue-50 text-blue-700"}`}>{e.recommendation}</span><span className="text-xs text-gray-400">{e.evaluated_at}</span></div>
            </div>;
          })}
        </div>}
        <div className="border-t pt-4 space-y-3">
          <div className="flex gap-2 items-start">
            <div className="flex-1"><input className="w-full border rounded-lg px-3 py-2 text-xs" placeholder="主管反馈（可选）" value={managerNote} onChange={e=>setManagerNote(e.target.value)}/></div>
            <button onClick={()=>handleGenerateEval(managerNote)} disabled={evalLoading} className="px-4 py-2 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 whitespace-nowrap">{evalLoading?"AI分析中...":"AI生成评估"}</button>
          </div>
          <div className="flex gap-2 items-start">
            <div className="flex-1"><input className="w-full border rounded-lg px-3 py-2 text-xs" placeholder="快速记录" value={managerNote} onChange={e=>setManagerNote(e.target.value)} onKeyDown={e=>e.key==="Enter"&&handleManualEval()}/></div>
            <button onClick={handleManualEval} disabled={evalLoading||!managerNote.trim()} className="px-4 py-2 text-xs border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 disabled:opacity-50 whitespace-nowrap">快速记录</button>
          </div>
        </div>
      </div>
    </div>}

    {/* Past evals for regular employees */}
    {emp.status!=="probation"&&probation?.evaluations?.length>0&&<div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">试用期评估历史</h3></div><div className="p-6 space-y-3">{probation.evaluations.map((e:any,i:number)=>{const avgScore=e.scores?Math.round((e.scores.adaption+e.scores.performance+e.scores.collaboration+e.scores.potential)/4*10)/10:0;return<div key={i} className="bg-gray-50 rounded-lg p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="text-sm font-medium">{e.stage}</span><span className={`text-xs px-2 py-0.5 rounded-full ${e.generated_by==="ai"?"bg-purple-100 text-purple-700":"bg-blue-100 text-blue-700"}`}>{e.generated_by==="ai"?"AI":"主管"}</span></div><span className="text-sm font-bold text-gray-600">{avgScore}/5</span></div><p className="text-sm text-gray-600 mt-1">{e.summary||e.strengths?.slice(0,80)}</p></div>;})}</div></div>}

    {/* Basic Info */}
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-6 py-3 bg-gray-50 border-b flex items-center justify-between"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">基本信息</h3>{editing&&<div className="flex items-center gap-2"><label className="text-xs text-gray-400">状态</label><select className={`${selectCls} w-auto`} value={form.status} onChange={e=>update("status",e.target.value)}>{statusOptions.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></div>}</div>
      <div className="p-6 grid grid-cols-2 gap-4 text-sm">
        <Field label="姓名" value={emp.name} editing={false}/>
        <Field label="身份证号" value={emp.id_number} editing={editing}><input className={inputCls} value={form.id_number} onChange={e=>update("id_number",e.target.value)}/></Field>
        <Field label="手机号" value={emp.phone} editing={false}/>
        <Field label="邮箱" value={emp.email} editing={false}/>
        <Field label="入职日期" value={emp.hire_date} editing={false}/>
        <Field label="转正日期" value={emp.probation_end_date?`${emp.probation_end_date}${emp.days_until_probation_end!=null&&emp.status==="probation"?` (${emp.days_until_probation_end}天后)`:""}`:"—"} editing={false}/>
      </div>
    </div>

    {/* Job Info */}
    <div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">岗位信息</h3></div>
      <div className="p-6 grid grid-cols-2 gap-4 text-sm">
        <Field label="岗位" value={emp.position} editing={editing}><input className={inputCls} value={form.position} onChange={e=>update("position",e.target.value)}/></Field>
        <Field label="部门" value={emp.department} editing={editing}><input className={inputCls} value={form.department} onChange={e=>update("department",e.target.value)}/></Field>
        <Field label="汇报对象" value={emp.reports_to} editing={editing}><input className={inputCls} value={form.reports_to} onChange={e=>update("reports_to",e.target.value)}/></Field>
        <Field label="薪资" value={emp.salary} editing={editing}><input className={inputCls} value={form.salary} onChange={e=>update("salary",e.target.value)} placeholder="如：25K×14薪"/></Field>
        <Field label="合同类型" value={emp.contract_type==="fulltime"?"全职":emp.contract_type==="parttime"?"兼职":emp.contract_type==="intern"?"实习":emp.contract_type} editing={editing}><select className={selectCls} value={form.contract_type} onChange={e=>update("contract_type",e.target.value)}>{contractOptions.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></Field>
        <Field label="合同到期" value={emp.contract_end_date} editing={editing}><input type="date" className={inputCls} value={form.contract_end_date} onChange={e=>update("contract_end_date",e.target.value)}/></Field>
      </div>
    </div>

    {/* 社保公积金 */}
    <div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">社保公积金</h3></div>
      <div className="p-6 grid grid-cols-2 gap-4 text-sm">
        <Field label="社保状态" value={emp.social_insurance==="active"?"已缴纳":emp.social_insurance==="pending"?"待办理":"不适用"} editing={editing}><select className={selectCls} value={form.social_insurance} onChange={e=>update("social_insurance",e.target.value)}>{siOptions.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></Field>
        <Field label="社保账号" value={emp.social_insurance_account} editing={editing}><input className={inputCls} value={form.social_insurance_account} onChange={e=>update("social_insurance_account",e.target.value)}/></Field>
        <Field label="公积金状态" value={emp.housing_fund==="active"?"已缴纳":emp.housing_fund==="pending"?"待办理":"不适用"} editing={editing}><select className={selectCls} value={form.housing_fund} onChange={e=>update("housing_fund",e.target.value)}>{siOptions.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></Field>
        <Field label="公积金账号" value={emp.housing_fund_account} editing={editing}><input className={inputCls} value={form.housing_fund_account} onChange={e=>update("housing_fund_account",e.target.value)}/></Field>
      </div>
    </div>

    {/* 学历信息 */}
    <div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">学历信息</h3></div>
      <div className="p-6 grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-gray-400 text-xs">最高学历</span><p className="font-medium">{emp.education_degree||"—"}</p></div>
        <div><span className="text-gray-400 text-xs">毕业院校</span><p className="font-medium">{emp.education_school||"—"}</p></div>
        <div><span className="text-gray-400 text-xs">专业</span><p className="font-medium">{emp.education_major||"—"}</p></div>
        <div><span className="text-gray-400 text-xs">毕业年份</span><p className="font-medium">{emp.education_graduation_year||"—"}</p></div>
        {emp.diploma_file&&<div className="col-span-2"><span className="text-gray-400 text-xs">学历证书</span><a href={`/api/employees/${emp.id}/file?type=diploma`} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-xs hover:underline ml-2">✓ 已上传 (点击查看 &rarr;)</a></div>}
        {emp.id_card_file&&<div className="col-span-2"><span className="text-gray-400 text-xs">身份证扫描件</span><a href={`/api/employees/${emp.id}/file?type=id_card`} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-xs hover:underline ml-2">✓ 已上传 (点击查看 &rarr;)</a></div>}
      </div>
    </div>

    {/* 银行卡 + 紧急联系人 */}
    <div className="grid grid-cols-2 gap-6">
      <div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">银行卡</h3></div><div className="p-6 space-y-3 text-sm"><Field label="开户行" value={emp.bank_name} editing={editing}><input className={inputCls} value={form.bank_name} onChange={e=>update("bank_name",e.target.value)}/></Field><Field label="卡号" value={emp.bank_account} editing={editing}><input className={`${inputCls} font-mono`} value={form.bank_account} onChange={e=>update("bank_account",e.target.value)}/></Field></div></div>
      <div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">紧急联系人</h3></div><div className="p-6 space-y-3 text-sm"><Field label="姓名" value={emp.emergency_contact_name} editing={editing}><input className={inputCls} value={form.emergency_contact_name} onChange={e=>update("emergency_contact_name",e.target.value)}/></Field><Field label="关系" value={emp.emergency_contact_relation} editing={editing}><input className={inputCls} value={form.emergency_contact_relation} onChange={e=>update("emergency_contact_relation",e.target.value)}/></Field><Field label="电话" value={emp.emergency_contact_phone} editing={editing}><input className={inputCls} value={form.emergency_contact_phone} onChange={e=>update("emergency_contact_phone",e.target.value)}/></Field></div></div>
    </div>

    {/* 备注 */}
    {(editing||emp.notes)&&<div className="bg-white rounded-xl border overflow-hidden"><div className="px-6 py-3 bg-gray-50 border-b"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">备注</h3></div><div className="p-6">{editing?<textarea className={`${inputCls} w-full`} rows={3} placeholder="内部备注" value={form.notes} onChange={e=>update("notes",e.target.value)}/>:<p className="text-sm text-gray-700">{emp.notes}</p>}</div></div>}

    {/* 入职登记状态 */}
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-6 py-3 bg-gray-50 border-b flex items-center justify-between"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">入职登记状态</h3>{emp.onboard_token_status==="expired"&&emp.onboard_completed!=="Y"&&<span className="text-xs text-red-500 font-medium">链接已过期</span>}</div>
      <div className="p-6 space-y-3">
        <div className="flex items-center gap-3">
          <span className={`text-sm px-3 py-1 rounded-full ${emp.onboard_completed==="Y"?"bg-green-50 text-green-700 border border-green-200":emp.onboard_token_status==="expired"?"bg-red-50 text-red-700 border border-red-200":"bg-gray-50 text-gray-500 border border-gray-200"}`}>{emp.onboard_completed==="Y"?"✓ 员工已填写":emp.onboard_token_status==="expired"?"✗ 已过期":"○ 待员工填写"}</span>
          {emp.onboard_completed!=="Y"&&emp.onboard_token_status!=="expired"&&<span className="text-xs text-gray-400">链接有效期内，员工填写后自动更新</span>}
        </div>
        {emp.onboard_token&&emp.onboard_completed!=="Y"&&<div className="bg-gray-50 rounded-lg p-3 space-y-2">
          <div className="flex gap-2"><span className="text-xs text-gray-400 w-16">链接</span><input className="flex-1 text-xs border rounded px-2 py-1 bg-white" value={`http://localhost:3000/onboarding/${emp.onboard_token}`} readOnly/><button onClick={()=>{navigator.clipboard.writeText(`http://localhost:3000/onboarding/${emp.onboard_token}`);alert("已复制");}} className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 whitespace-nowrap">复制</button></div>
          {emp.onboard_token_created_at&&<div className="flex gap-2 text-xs text-gray-400"><span className="w-16">有效期</span><span>{emp.onboard_token_created_at?.slice(0,10)} ~ {emp.onboard_token_expires_at?.slice(0,10)}（7天）</span></div>}
          <div className="flex gap-2 pt-1">
            <button onClick={handleRegenerateToken} disabled={regenerating} className="px-3 py-1.5 text-xs border border-gray-300 text-gray-600 rounded hover:bg-gray-100 disabled:opacity-50">{regenerating?"生成中...":emp.onboard_token_status==="expired"?"重新生成 · 已过期":"重新生成链接"}</button>
            {emp.onboard_token_status==="expired"&&<span className="text-xs text-red-400 self-center">旧链接已过期，重新生成后可发给员工</span>}
          </div>
        </div>}
      </div>
    </div>

    {/* 招聘质量分析 */}
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-6 py-3 bg-gray-50 border-b flex items-center justify-between"><h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">招聘质量分析</h3>{!feedbackLoop&&<button onClick={fetchFeedbackLoop} disabled={feedbackLoading} className="text-xs text-blue-600 hover:underline">{feedbackLoading?"生成中...":"生成报告"}</button>}</div>
      {feedbackLoop?.feedback&&<div className="p-6 space-y-4">
        <div className={`rounded-lg p-4 ${feedbackLoop.feedback.hiring_quality==="excellent"?"bg-green-50 border border-green-200":feedbackLoop.feedback.hiring_quality==="good"?"bg-blue-50 border border-blue-200":feedbackLoop.feedback.hiring_quality==="acceptable"?"bg-yellow-50 border border-yellow-200":"bg-red-50 border border-red-200"}`}>
          <div className="flex items-center justify-between"><div><p className="text-sm font-bold">招聘质量：{feedbackLoop.feedback.hiring_quality==="excellent"?"优秀":feedbackLoop.feedback.hiring_quality==="good"?"良好":feedbackLoop.feedback.hiring_quality==="acceptable"?"可接受":"待改进"}</p><p className="text-xs mt-1 text-gray-600">{feedbackLoop.feedback.overall_assessment}</p></div><span className={`text-xs px-2 py-0.5 rounded-full ${feedbackLoop.feedback.prediction_accuracy==="accurate"?"bg-green-100 text-green-700":feedbackLoop.feedback.prediction_accuracy==="partial"?"bg-yellow-100 text-yellow-700":"bg-red-100 text-red-700"}`}>AI预测：{feedbackLoop.feedback.prediction_accuracy==="accurate"?"准确":feedbackLoop.feedback.prediction_accuracy==="partial"?"部分准确":"偏差较大"}</span></div>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-50 rounded-lg p-4"><p className="text-xs font-medium text-gray-400 mb-2">AI 招聘时预测</p><div className="flex items-center gap-2 mb-2"><span className="text-lg font-bold text-yellow-500">{"★".repeat(feedbackLoop.feedback.computed?.ai_star||0)}</span><span className="text-xs text-gray-400">{feedbackLoop.feedback.computed?.ai_star}/5 星</span></div>{feedbackLoop.feedback.computed?.interview_rating&&<p className="text-xs text-gray-500">面试评分: {feedbackLoop.feedback.computed.interview_rating}/5</p>}</div>
          <div className="bg-gray-50 rounded-lg p-4"><p className="text-xs font-medium text-gray-400 mb-2">入职后实际表现</p><div className="flex items-center gap-2 mb-2"><span className="text-lg font-bold text-green-600">{feedbackLoop.feedback.computed?.probation_avg?.toFixed(1)||"—"}/5</span></div><p className="text-xs text-gray-500">{feedbackLoop.feedback.computed?.evaluation_count||0} 次试用期评估</p></div>
        </div>
        <div className="grid grid-cols-2 gap-4">{feedbackLoop.feedback.validated_strengths?.length>0&&<div><p className="text-xs font-medium text-green-600 mb-1">✓ 被验证的优势</p>{feedbackLoop.feedback.validated_strengths.map((s:string,i:number)=><p key={i} className="text-xs text-gray-600 ml-2">· {s}</p>)}</div>}{feedbackLoop.feedback.missed_risks?.length>0&&<div><p className="text-xs font-medium text-orange-600 mb-1">⚠ AI未预见的问题</p>{feedbackLoop.feedback.missed_risks.map((s:string,i:number)=><p key={i} className="text-xs text-gray-600 ml-2">· {s}</p>)}</div>}</div>
        {feedbackLoop.feedback.lesson&&<div className="bg-purple-50 rounded-lg p-3 text-xs"><p className="font-medium text-purple-700 mb-0.5">经验教训</p><p className="text-purple-800">{feedbackLoop.feedback.lesson}</p></div>}
      </div>}
      {!feedbackLoop?.feedback&&!feedbackLoading&&<div className="p-6 text-center text-xs text-gray-400">点击"生成报告"对比 AI 招聘预测与员工实际表现</div>}
      {feedbackLoading&&<div className="p-6 text-center"><div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"/><p className="text-xs text-gray-400">AI 正在生成招聘质量分析...</p></div>}
    </div>

    {/* Sticky save bar */}
    {editing&&<div className="sticky bottom-4 bg-white border shadow-lg rounded-xl p-4 flex items-center justify-between"><p className="text-sm text-gray-500">编辑员工信息</p><div className="flex gap-2"><button onClick={cancelEdit} className="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">取消</button><button onClick={handleSave} disabled={saving} className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">{saving?"保存中...":"保存修改"}</button></div></div>}
  </div>;
}
