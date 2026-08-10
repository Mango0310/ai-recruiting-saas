"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import axios from "axios";

const API = "/api";

export default function OnboardingPage() {
  const { token } = useParams<{ token: string }>();
  const [loading, setLoading] = useState(true);
  const [employee, setEmployee] = useState<any>(null);
  const [form, setForm] = useState({
    phone: "", email: "", id_number: "",
    education_degree: "", education_school: "", education_major: "",
    education_graduation_year: 0,
    bank_name: "", bank_account: "",
    social_insurance_account: "", housing_fund_account: "",
    emergency_contact_name: "", emergency_contact_phone: "", emergency_contact_relation: "",
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState<Record<string, boolean>>({});
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/employees/token/${token}`)
      .then(res => {
        setEmployee(res.data);
        setForm({
          phone: res.data.phone || "",
          email: res.data.email || "",
          id_number: res.data.id_number || "",
          education_degree: res.data.education_degree || "",
          education_school: res.data.education_school || "",
          education_major: res.data.education_major || "",
          education_graduation_year: res.data.education_graduation_year || 0,
          bank_name: res.data.bank_name || "",
          bank_account: res.data.bank_account || "",
          social_insurance_account: res.data.social_insurance_account || "",
          housing_fund_account: res.data.housing_fund_account || "",
          emergency_contact_name: res.data.emergency_contact_name || "",
          emergency_contact_phone: res.data.emergency_contact_phone || "",
          emergency_contact_relation: res.data.emergency_contact_relation || "",
        });
      })
      .catch(() => setError("无效链接或链接已过期"))
      .finally(() => setLoading(false));
  }, [token]);

  const handleSubmit = async () => {
    setSaved(false);
    try {
      await axios.put(`${API}/employees/token/${token}`, { ...form, onboard_completed: true });
      setSaved(true);
    } catch {
      setError("保存失败，请重试");
    }
  };

  const handleFileUpload = async (file: File, docType: string) => {
    setUploading({ ...uploading, [docType]: true });
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("doc_type", docType);
      await axios.post(`${API}/employees/token/${token}/upload`, fd);
      setUploadedFiles({ ...uploadedFiles, [docType]: true });
    } catch {
      alert("上传失败");
    } finally {
      setUploading({ ...uploading, [docType]: false });
    }
  };

  if (loading) {
    return <div className="max-w-lg mx-auto py-20 text-center"><p className="text-gray-500">加载中...</p></div>;
  }

  if (error) {
    return <div className="max-w-lg mx-auto py-20 text-center"><p className="text-red-500">{error}</p></div>;
  }

  return (
    <div className="max-w-lg mx-auto py-10 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">入职信息登记</h1>
        <p className="text-gray-500 text-sm mt-1">
          {employee.name} · {employee.position} · {employee.department}
        </p>
      </div>

      {saved && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
          <p className="text-green-800 font-semibold">✓ 信息已提交</p>
          <p className="text-green-600 text-sm mt-1">HR 将根据你填写的信息办理入职手续</p>
        </div>
      )}

      <div className="bg-white rounded-xl border p-6 space-y-4">
        {/* Basic Info */}
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase mb-3">基本信息</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">姓名</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" value={employee.name} disabled />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">岗位</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" value={employee.position} disabled />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">手机号</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">邮箱</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-1">身份证号</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="请填写身份证号" value={form.id_number} onChange={e => setForm({...form, id_number: e.target.value})} />
            </div>
          </div>
        </div>

        {/* Education */}
        <div className="border-t pt-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-3">学历信息</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">最高学历</label>
              <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.education_degree}
                onChange={e => setForm({...form, education_degree: e.target.value})}>
                <option value="">请选择</option>
                <option value="博士">博士</option><option value="硕士">硕士</option>
                <option value="本科">本科</option><option value="大专">大专</option>
                <option value="其他">其他</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">毕业院校</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="学校全称"
                value={form.education_school} onChange={e => setForm({...form, education_school: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">专业</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="专业名称"
                value={form.education_major} onChange={e => setForm({...form, education_major: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">毕业年份</label>
              <input type="number" className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：2021"
                value={form.education_graduation_year || ""} onChange={e => setForm({...form, education_graduation_year: parseInt(e.target.value) || 0})} />
            </div>
          </div>

          {/* Document upload */}
          <div className="mt-3 space-y-2">
            <p className="text-xs text-gray-400">上传证明文件（图片或PDF，单个不超过5MB）</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  学历证书 {employee.diploma_file && <span className="text-green-500">✓ 已上传</span>}
                </label>
                <input type="file" accept=".pdf,.jpg,.png,.jpeg" className="w-full text-xs"
                  onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, "diploma"); }} />
                {uploading.diploma && <span className="text-xs text-blue-500">上传中...</span>}
                {(uploadedFiles.diploma || employee.diploma_file) && (
                  <a href={`${API}/employees/token/${token}/file?type=diploma`} target="_blank" rel="noopener noreferrer"
                     className="text-xs text-blue-600 hover:underline mt-1 inline-block">
                    预览已上传文件 &rarr;
                  </a>
                )}
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  身份证扫描件 {employee.id_card_file && <span className="text-green-500">✓ 已上传</span>}
                </label>
                <input type="file" accept=".pdf,.jpg,.png,.jpeg" className="w-full text-xs"
                  onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, "id_card"); }} />
                {uploading.id_card && <span className="text-xs text-blue-500">上传中...</span>}
                {(uploadedFiles.id_card || employee.id_card_file) && (
                  <a href={`${API}/employees/token/${token}/file?type=id_card`} target="_blank" rel="noopener noreferrer"
                     className="text-xs text-blue-600 hover:underline mt-1 inline-block">
                    预览已上传文件 &rarr;
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Bank */}
        <div className="border-t pt-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-3">银行卡信息（用于发薪）</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">开户行</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：招商银行" value={form.bank_name} onChange={e => setForm({...form, bank_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">银行卡号</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="请输入银行卡号" value={form.bank_account} onChange={e => setForm({...form, bank_account: e.target.value})} />
            </div>
          </div>
        </div>

        {/* 社保公积金账号 */}
        <div className="border-t pt-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-3">社保公积金信息</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">社保账号</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="个人社保编号（如不清楚可留空）"
                value={form.social_insurance_account} onChange={e => setForm({...form, social_insurance_account: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">公积金账号</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="个人公积金账号（如不清楚可留空）"
                value={form.housing_fund_account} onChange={e => setForm({...form, housing_fund_account: e.target.value})} />
            </div>
          </div>
        </div>

        {/* Emergency contact */}
        <div className="border-t pt-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-3">紧急联系人</p>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">姓名</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" value={form.emergency_contact_name} onChange={e => setForm({...form, emergency_contact_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">关系</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：配偶" value={form.emergency_contact_relation} onChange={e => setForm({...form, emergency_contact_relation: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">电话</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" value={form.emergency_contact_phone} onChange={e => setForm({...form, emergency_contact_phone: e.target.value})} />
            </div>
          </div>
        </div>

        <button onClick={handleSubmit} className="w-full py-3 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
          提交入职信息
        </button>
      </div>
    </div>
  );
}
