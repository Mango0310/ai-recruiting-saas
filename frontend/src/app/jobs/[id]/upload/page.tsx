"use client";

import { useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { uploadResumes } from "@/lib/api";

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter((f) => f.type === "application/pdf");
    setFiles((prev) => [...prev, ...dropped]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      const data = await uploadResumes(Number(id), files);
      setResults(data.results || []);
      if (data.succeeded > 0) {
        setFiles([]);
      }
    } catch (e) {
      alert("上传失败: " + (e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href={`/jobs/${id}`} className="text-gray-400 hover:text-gray-600">&larr; 返回岗位</Link>
        <h1 className="text-xl font-bold">上传简历</h1>
      </div>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 transition cursor-pointer"
        onClick={() => fileRef.current?.click()}
      >
        <p className="text-gray-500 text-lg">拖拽 PDF 文件到此处</p>
        <p className="text-gray-400 text-sm mt-1">或点击选择文件，支持批量上传</p>
        <input ref={fileRef} type="file" accept=".pdf" multiple className="hidden" onChange={handleFileChange} />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg border p-4 space-y-2">
          <h3 className="font-medium text-sm">待上传 ({files.length} 份)</h3>
          {files.map((f, i) => (
            <div key={i} className="flex justify-between items-center text-sm">
              <span>{f.name}</span>
              <button onClick={() => removeFile(i)} className="text-red-500 hover:text-red-700">移除</button>
            </div>
          ))}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {uploading ? "解析中..." : "开始解析"}
          </button>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg border p-4 space-y-2">
          <h3 className="font-medium text-sm">解析结果</h3>
          {results.map((r: any, i: number) => (
            <div key={i} className={`text-sm p-2 rounded ${r.status === "completed" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
              <span className="font-medium">{r.filename}</span>
              <span className="ml-2">
                {r.status === "completed"
                  ? `✓ 解析成功 — ${r.candidate_name}`
                  : `✗ ${r.error}`}
              </span>
            </div>
          ))}
          <button onClick={() => router.push(`/jobs/${id}`)} className="w-full py-2 border rounded-lg text-sm hover:bg-gray-50">
            返回候选人列表
          </button>
        </div>
      )}
    </div>
  );
}
