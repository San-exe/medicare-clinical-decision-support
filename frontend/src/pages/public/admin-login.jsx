import React, { useState } from "react";
import { ShieldCheck, Lock, HeartPulse, ArrowLeft, ArrowUpRight } from "lucide-react";
import { useLocation } from "wouter";
import { trpc } from "../../lib/trpc";

export default function AdminLogin() {
  const [, navigate] = useLocation();
  const [password, setPassword] = useState("");
  const mutation = trpc.auth.adminLogin.useMutation();

  const submit = async (event) => {
    event.preventDefault();
    try {
      await mutation.mutateAsync({ password });
      navigate("/admin/verification");
    } catch {}
  };

  return (
    <div className="min-h-screen bg-[#f7faf9] px-5 py-8 text-[#123d32] dark:bg-[#0b1210] dark:text-white">
      <div className="mx-auto max-w-[560px]">
        <button onClick={() => navigate("/login")} className="mb-8 flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-emerald-600"><ArrowLeft size={16} /> Back to sign in</button>
        <div className="rounded-[32px] border border-slate-200 bg-white p-8 shadow-[0_30px_80px_rgba(18,61,50,0.10)] dark:border-white/10 dark:bg-[#121c19]">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10"><ShieldCheck size={26} /></div>
          <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-emerald-600">Restricted access</p>
          <h1 className="mt-2 text-4xl font-black tracking-[-0.05em]">Admin console</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">Review doctor verification requests and platform audit activity. Clinical records are not displayed here.</p>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <label className="block text-sm font-bold">Administrator password</label>
            <div className="relative"><Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} /><input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required className="h-13 w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 outline-none focus:border-emerald-500 dark:border-white/10 dark:bg-white/5" placeholder="Enter admin password" /></div>
            {mutation.error && <p className="text-sm font-semibold text-red-600">{mutation.error.message}</p>}
            <button disabled={mutation.isPending} className="flex h-13 w-full items-center justify-center gap-3 rounded-2xl bg-[#0d4639] font-bold text-white transition hover:bg-[#0a3b30] disabled:opacity-60">
              {mutation.isPending ? "Signing in…" : "Enter admin console"}<span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[#0d4639]"><ArrowUpRight size={17} /></span>
            </button>
          </form>
          <div className="mt-8 flex items-center gap-2 text-xs text-slate-500"><HeartPulse size={14} className="text-emerald-500" /> Secure administrative authentication</div>
        </div>
      </div>
    </div>
  );
}
