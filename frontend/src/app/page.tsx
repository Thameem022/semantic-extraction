"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

type Candidate = {
  fieldId: string;
  rawValue?: string;
  normalizedValue?: string;
};

type StatusResponse =
  | { docId: string; filename?: string; status: string }
  | { docId: string; filename?: string; status: string; candidates: Candidate[] };

const FUNCTION_BASE_FALLBACK = "http://localhost:7071";

const STATUS_STEPS: Array<{ key: string; label: string }> = [
  { key: "RECEIVED", label: "Received" },
  { key: "OCR_STARTED", label: "OCR Started" },
  { key: "OCR_COMPLETE", label: "OCR Complete" },
  { key: "CANDIDATES_GENERATED", label: "Results Ready" },
];

const FIELD_LABELS: Array<{ id: string; label: string }> = [
  { id: "applicant_name", label: "Applicant Name" },
  { id: "insured_address", label: "Insured Address" },
  { id: "policy_number", label: "Policy Number" },
  { id: "effective_date", label: "Effective Date" },
  { id: "naics_code", label: "NAICS Code" },
  { id: "sic_naics_code", label: "SIC/NAICS Code" },
  { id: "year_established", label: "Year Established" },
  { id: "telephone_number", label: "Telephone Number" },
  { id: "email_address", label: "Email Address" },
  { id: "website", label: "Website" },
  { id: "business_description", label: "Business Description" },
  { id: "emp_full_time", label: "Full-Time Employees" },
  { id: "emp_part_time", label: "Part-Time Employees" },
  { id: "emp_independent_contractors", label: "Independent Contractors" },
  { id: "emp_temporary_leased", label: "Temporary/Leased Employees" },
  { id: "emp_full_time_ca", label: "Full-Time Employees (CA)" },
  { id: "emp_part_time_ca", label: "Part-Time Employees (CA)" },
  { id: "total_assets", label: "Total Assets" },
  { id: "net_income", label: "Net Income / Net Loss" },
  { id: "revenue", label: "Revenue" },
  { id: "profit", label: "Profit / Operating Income" },
  { id: "limit_employment_practices", label: "Limit (Employment Practices)" },
  { id: "retention_employment_practices", label: "Retention (Employment Practices)" },
];

function getStepIndex(status: string | null): number {
  if (!status) return -1;
  return STATUS_STEPS.findIndex((s) => s.key === status);
}

function candidatesToFieldMap(candidates: Candidate[] | null): Record<string, string> {
  const out: Record<string, string> = {};
  if (!candidates) return out;
  for (const c of candidates) {
    if (!c?.fieldId) continue;
    const value = (c.normalizedValue ?? c.rawValue ?? "").toString();
    if (value.trim()) out[c.fieldId] = value;
  }
  return out;
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [docId, setDocId] = useState<string | null>(null);
  const [displayFilename, setDisplayFilename] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[] | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const functionBaseUrl =
    process.env.NEXT_PUBLIC_FUNCTION_BASE_URL ?? FUNCTION_BASE_FALLBACK;
  const uploadUrl = `${functionBaseUrl}/api/fn_http_upload`;

  const statusUrl = docId
    ? `${functionBaseUrl}/api/fn_http_status?docId=${encodeURIComponent(docId)}`
    : null;

  const activeStepIndex = getStepIndex(status);
  const fieldMap = useMemo(() => candidatesToFieldMap(candidates), [candidates]);

  const canPoll = !!docId && !candidates;
  const shouldStopPolling = useMemo(() => {
    if (!status) return false;
    if (status === "CANDIDATES_GENERATED") return false;
    return status.endsWith("_FAILED");
  }, [status]);

  useEffect(() => {
    if (!canPoll) return;
    if (shouldStopPolling) return;
    if (!statusUrl) return;

    let cancelled = false;

    const poll = async () => {
      try {
        const resp = await fetch(statusUrl, { method: "GET" });
        if (!resp.ok) {
          throw new Error(`Status request failed: ${resp.status}`);
        }
        const data = (await resp.json()) as StatusResponse;

        if (cancelled) return;
        if (data.filename) setDisplayFilename(data.filename);
        setStatus(data.status);

        const maybeCandidates = (data as { candidates?: unknown }).candidates;
        if (Array.isArray(maybeCandidates)) {
          setCandidates(maybeCandidates as Candidate[]);
        }
      } catch (e: unknown) {
        if (cancelled) return;
        setPollingError(e instanceof Error ? e.message : String(e));
      }
    };

    const timerId = window.setInterval(poll, 2500);
    // immediate first poll
    poll();

    return () => {
      cancelled = true;
      window.clearInterval(timerId);
    };
  }, [canPoll, shouldStopPolling, statusUrl]);

  const reset = () => {
    setDocId(null);
    setDisplayFilename(null);
    setStatus(null);
    setCandidates(null);
    setPollingError(null);
    setUploadError(null);
    setIsUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleFile = async (file: File) => {
    setUploadError(null);
    setPollingError(null);
    setCandidates(null);
    setStatus(null);
    setDocId(null);
    setDisplayFilename(file.name);

    if (!file) return;

    const looksPdf =
      file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!looksPdf) {
      setUploadError("Please upload a PDF file.");
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file, file.name);

      const resp = await fetch(uploadUrl, {
        method: "POST",
        body: formData,
      });

      if (!resp.ok) {
        const text = await resp.text().catch(() => "");
        throw new Error(text || `Upload failed: ${resp.status}`);
      }

      const data = (await resp.json()) as { docId: string; filename?: string };
      setDocId(data.docId);
      if (data.filename) setDisplayFilename(data.filename);
      setStatus("RECEIVED");
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void handleFile(file);
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <header className="mb-6">
          <h1 className="text-3xl font-semibold tracking-tight">Semantic Extraction</h1>
          <p className="mt-2 text-zinc-600">
            Upload an insurance PDF, track progress, and view extracted fields.
          </p>
        </header>

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          {!docId && (
            <div>
              <div
                className={[
                  "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition",
                  isDragging ? "border-emerald-500 bg-emerald-50" : "border-zinc-200 bg-zinc-50",
                ].join(" ")}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragEnter={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                }}
                onDrop={onDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleFile(file);
                  }}
                />

                <div className="max-w-md">
                  <div className="text-sm font-medium text-zinc-700">
                    Drag and drop your PDF here
                  </div>
                  <div className="mt-2 text-zinc-500">
                    Or{" "}
                    <button
                      type="button"
                      className="font-medium text-emerald-700 underline underline-offset-2"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading}
                    >
                      browse
                    </button>
                  </div>
                  <div className="mt-4 text-xs text-zinc-500">
                    Backend endpoint:{" "}
                    <span className="font-mono">{uploadUrl.replace(/^https?:\/\//, "")}</span>
                  </div>
                </div>
              </div>

              {uploadError && (
                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {uploadError}
                </div>
              )}
            </div>
          )}

          {!!docId && !candidates && (
            <div>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm text-zinc-500">Tracking file</div>
                  <div className="text-sm font-medium">{displayFilename || docId}</div>
                  <div className="mt-1 text-sm text-zinc-600">
                    Status:{" "}
                    <span className="font-medium text-zinc-900">
                      {status ?? "—"}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {(isUploading || pollingError) && (
                    <div className="text-sm text-zinc-600">
                      {pollingError ? pollingError : "Working…"}
                    </div>
                  )}
                  <button
                    type="button"
                    className="rounded-lg border bg-white px-3 py-2 text-sm hover:bg-zinc-50"
                    onClick={reset}
                  >
                    Upload another
                  </button>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-start">
                  {STATUS_STEPS.map((s, idx) => {
                    const done = idx < activeStepIndex;
                    const active = idx === activeStepIndex;
                    const circleClass = done
                      ? "border-emerald-600 bg-emerald-600 text-white"
                      : active
                      ? "border-emerald-600 bg-emerald-50 text-emerald-700"
                      : "border-zinc-300 bg-white text-zinc-500";

                    return (
                      <React.Fragment key={s.key}>
                        <div className="flex w-full flex-col items-center">
                          <div
                            className={[
                              "flex h-10 w-10 items-center justify-center rounded-full border text-sm font-semibold transition",
                              circleClass,
                            ].join(" ")}
                            aria-label={s.label}
                          >
                            {done ? "✓" : idx + 1}
                          </div>
                          <div className="mt-2 text-center text-xs text-zinc-600">
                            {s.label}
                          </div>
                        </div>
                        {idx < STATUS_STEPS.length - 1 && (
                          <div className="mt-5 flex flex-1 px-1">
                            <div
                              className={[
                                "h-0.5 w-full rounded",
                                idx < activeStepIndex
                                  ? "bg-emerald-600"
                                  : "bg-zinc-200",
                              ].join(" ")}
                            />
                          </div>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {pollingError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {pollingError}
                </div>
              )}

              {status && status.endsWith("_FAILED") && (
                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  Processing failed with status: {status}
                </div>
              )}
            </div>
          )}

          {candidates && (
            <div>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm text-zinc-500">Extraction complete</div>
                  <div className="text-sm font-medium">{displayFilename || docId}</div>
                </div>
                <button
                  type="button"
                  className="rounded-lg border bg-white px-3 py-2 text-sm hover:bg-zinc-50"
                  onClick={reset}
                >
                  Upload another
                </button>
              </div>

              <div className="mb-4 flex flex-col gap-1">
                <div className="text-sm font-medium">Extracted Fields</div>
                <div className="text-xs text-zinc-500">
                  Values are taken from each candidate’s `normalizedValue` (fallback: `rawValue`).
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border">
                <table className="min-w-full text-sm">
                  <tbody>
                    {FIELD_LABELS.map((f) => {
                      const value = fieldMap[f.id];
                      return (
                        <tr key={f.id} className="border-t last:border-b">
                          <td className="w-64 bg-zinc-50 px-4 py-3 font-medium text-zinc-700">
                            {f.label}
                          </td>
                          <td className="px-4 py-3 text-zinc-900">
                            {value ? (
                              <span className="whitespace-pre-wrap break-words">
                                {value}
                              </span>
                            ) : (
                              <span className="text-zinc-400">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <details className="mt-6 rounded-xl border bg-white p-4">
                <summary className="cursor-pointer text-sm font-medium text-zinc-700">
                  View raw candidates JSON
                </summary>
                <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-words text-xs text-zinc-800">
                  {JSON.stringify(candidates, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
