import { FormEvent, useState } from 'react';
import { Check, ChevronLeft, ChevronRight, FileText, LockKeyhole, LogOut, Search, ShieldCheck, Sparkles, Upload } from 'lucide-react';

const steps = ['LOGIN', 'UPLOAD THE JD', 'UPLOAD CVS', 'STACK RANKING', 'SCREENING QUESTIONS', 'HIRING MARKET INSIGHTS', 'SEARCH STRINGS'];
const files = ['Aarav', 'Bhavna', 'Chirag', 'Divya', 'Eshaan'];
const ranking = [
  ['1', 'Candidate C', '94', '8 yrs; Cloud, AWS, Python, distributed systems', 'FastAPI, PostgreSQL depth', 'Strong cloud evidence and seniority; validate framework/database depth.'],
  ['2', 'Candidate A', '92', '5.5 yrs; Python, FastAPI, PostgreSQL, AWS, Docker', 'Scale ownership, architecture breadth', 'Excellent direct match for the role requirements.'],
  ['3', 'Candidate E', '84', '6 yrs; Python, Flask, PostgreSQL, AWS', 'FastAPI, Docker depth', 'Strong backend foundation with transferable framework experience.'],
  ['4', 'Candidate B', '72', '4 yrs; Python, Django, Docker', 'FastAPI, AWS, PostgreSQL depth', 'Relevant experience; verify seniority against the 5+ year brief.'],
  ['5', 'Candidate D', '45', '2 yrs; Python, FastAPI', 'PostgreSQL, AWS, Docker, seniority', 'Promising framework exposure but below the experience requirement.'],
];
const questions = [
  ['Technical Architecture', 'How would you design an async FastAPI service that handles slow external calls?', 'Use async clients, bounded concurrency, timeouts, retries, circuit breakers, and observability.'],
  ['Technical Architecture', 'How do PostgreSQL indexes improve performance, and when can they hurt?', 'Use query plans and selectivity; account for write cost and avoid redundant indexes.'],
  ['Technical Architecture', 'How do you containerize a Python service with Docker?', 'Use a small pinned image, multi-stage build, non-root user, health check, and reproducible dependencies.'],
  ['Technical Architecture', 'Describe a production AWS deployment for a backend API.', 'Cover VPC, load balancing, compute, managed database, secrets, autoscaling, monitoring, and rollback.'],
  ['Experience & System Design', 'How would you prepare a system for a tenfold traffic increase?', 'Measure bottlenecks, cache safely, scale stateless services, tune the database, queue where useful, and load test.'],
  ['Experience & System Design', 'When would you choose microservices over a modular monolith?', 'Base it on team boundaries, deployment independence, scale, and operational cost.'],
  ['Experience & System Design', 'How would you execute a zero-downtime database migration?', 'Use expand-and-contract, compatibility, backfill, validation, and a rollback plan.'],
  ['Fit & Stakeholder', 'What makes a code review useful?', 'Specific, respectful feedback focused on correctness, maintainability, security, and tests.'],
  ['Fit & Stakeholder', 'How do you maintain discipline while working remotely?', 'Clear priorities, written updates, focused work blocks, and proactive communication.'],
  ['Fit & Stakeholder', 'How do you resolve disagreement with another engineering team?', 'Align on outcomes, bring evidence, document trade-offs, decide explicitly, and preserve trust.'],
];
const market = [['Razorpay', '5–10 years', '₹35–55 LPA base CTC', 'Bengaluru / Remote'], ['PhonePe', '5–10 years', '₹35–60 LPA base CTC', 'Bengaluru'], ['Swiggy', '5–9 years', '₹32–52 LPA base CTC', 'Bengaluru / Remote'], ['Enterprise SaaS Product Firms', '5–10 years', '₹28–48 LPA base CTC', 'Bengaluru / Remote']];

export default function RecruitmentPage() {
  const [step, setStep] = useState(1);
  const [parsed, setParsed] = useState<string[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState<'sign-in' | 'sign-up'>('sign-in');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const user = { full_name: 'Senior Recruiter' };
  const logout = () => {
    setIsAuthenticated(false);
    setStep(1);
    setParsed([]);
    setPassword('');
  };
  function handleAuthentication(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (authMode === 'sign-up' && !fullName.trim()) {
      setAuthError('Enter your full name to create an account.');
      return;
    }
    if (!email.includes('@')) {
      setAuthError('Enter a valid work email address.');
      return;
    }
    if (password.length < 8) {
      setAuthError('Password must be at least 8 characters.');
      return;
    }
    setAuthError(null);
    setIsAuthenticated(true);
  }
  const go = (value: number) => {
    if (value > step + 1 || (value >= 4 && parsed.length < 5)) return;
    setStep(Math.max(1, Math.min(7, value)));
  };
  const header = <div className="workspace-top"><div><span className="eyebrow">Step {String(step).padStart(2, '0')} of 07</span><h2>{steps[step - 1]}</h2></div><div className="top-actions"><button className="secondary-button" disabled={step === 1} onClick={() => go(step - 1)}><ChevronLeft size={16} /> Back</button><button className="primary-button" disabled={step === 7 || (step === 3 && parsed.length < 5)} onClick={() => go(step + 1)}>Continue <ChevronRight size={16} /></button></div></div>;
  const content = [
    <section className="welcome-panel"><div className="welcome-art"><ShieldCheck size={54} /></div><div><span className="eyebrow">Enterprise authentication</span><h3>Recruiter session active.</h3><p className="auth-banner">[SUCCESS] Recruiter Signed In | Workstation: TA Enterprise Suite | Authenticated User: Senior Recruiter</p><p>Recine AI processes this recruitment brief in strict numerical order.</p><button className="primary-button" onClick={() => go(2)}>Begin Step 2: Upload the JD <ChevronRight size={16} /></button></div></section>,
    <section className="content-grid"><div className="panel large-panel"><div className="panel-heading"><div><span className="eyebrow">Step 2 · Structured intake</span><h3>Upload the JD</h3></div><FileText size={20} /></div><textarea className="large-textarea" defaultValue={'Senior Backend Engineer\nKey Skills: Python, FastAPI, PostgreSQL, AWS, Docker\nExperience Required: 5+ Years\nHiring Location: Bengaluru / Remote'} /><button className="primary-button" onClick={() => go(3)}>Parse and continue <Sparkles size={16} /></button></div><div className="panel parsed-card"><span className="eyebrow">What Recine understood</span><h3>JD summary</h3><table className="data-table"><tbody><tr><th>Role</th><td>Senior Backend Engineer</td></tr><tr><th>Key Skills</th><td>Python, FastAPI, PostgreSQL, AWS, Docker</td></tr><tr><th>Experience Required</th><td>5+ Years</td></tr><tr><th>Hiring Location</th><td>Bengaluru / Remote</td></tr></tbody></table></div></section>,
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Step 3 · Ingestion log</span><h3>Upload CVs</h3></div><span className="count-badge">{parsed.length} / 5 parsed</span></div><div className="ingestion-log">{files.map((file) => <div className="ingestion-row" key={file}><span className="log-check">{parsed.includes(file) ? <Check size={13} /> : <Upload size={13} />}</span><div><strong>{file}</strong><span>Applicant resume ready for ingestion</span></div><label className="upload-action"><input type="file" accept=".pdf,.doc,.docx" onChange={() => setParsed((current) => current.includes(file) ? current : [...current, file])} />{parsed.includes(file) ? 'Parsed' : 'Attach CV'}</label></div>)}</div><div className="verification"><Check size={17} /><span><strong>Read Log:</strong> {parsed.length === 5 ? '5 Resumes Parsed Successfully. Stack ranking is now unlocked.' : `${parsed.length} of 5 resumes parsed successfully. Attach all five CVs to unlock stack ranking.`}</span></div></section>,
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Step 4 · Evidence-based evaluation</span><h3>Stack Ranking</h3></div><span className="secure-badge"><ShieldCheck size={15} /> Bias-free scoring</span></div><p className="muted">Rankings use CV evidence only. Do not use name, gender, age, photo, or marital status.</p><div className="ranking-table"><div className="table-head"><span>Rank</span><span>Candidate ID</span><span>Score (/100)</span><span>Matched Skills</span><span>Missing Skills</span><span>Short Reason / Justification</span></div>{ranking.map((row) => <div className="table-row ranking-row" key={row[1]}>{row.map((cell, index) => <span className={index === 0 ? 'rank-number' : index === 2 ? 'score-value' : index === 4 ? 'missing-text' : ''} key={cell}>{cell}</span>)}</div>)}</div></section>,
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Step 5 · Recruiter call guide</span><h3>10 Screening Questions</h3></div><Search size={20} /></div><div className="question-list">{questions.map(([category, question, answer], index) => <article className="question-row" key={question}><span className="question-number">{String(index + 1).padStart(2, '0')}</span><div><span className="question-type">{category}</span><h4>{question}</h4><p><strong>Good candidate answer:</strong> {answer}</p></div></article>)}</div></section>,
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Step 6 · Hiring market scan</span><h3>Senior Backend Engineer (Python/FastAPI, 5+ yrs)</h3></div><span className="estimate-badge">AI estimate</span></div><p className="muted">Bengaluru / Remote competitor benchmark.</p><div className="market-table"><div className="table-head"><span>Company Name</span><span>Experience Range</span><span>Compensation Range (Base CTC)</span><span>Hiring Location</span></div>{market.map((row) => <div className="table-row" key={row[0]}>{row.map((cell) => <span key={cell}>{cell}</span>)}</div>)}</div><p className="source-disclaimer">Data source: Estimated via AI web search and public job postings.</p></section>,
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Step 7 · Candidate discovery</span><h3>Search Strings</h3></div><span className="count-badge">4 recruiter-ready strings</span></div>{[['LinkedIn Recruiter - Boolean Version', '("Senior Backend Engineer" OR "Backend Engineer") AND (Python AND FastAPI) AND (PostgreSQL OR SQL) AND (AWS OR Docker)'], ['LinkedIn Recruiter - Plain Non-Boolean Version', 'Senior Backend Engineer Python FastAPI PostgreSQL AWS Docker Bengaluru Remote'], ['Naukri.com - Boolean Version', '("Senior Backend Developer" OR "Backend Engineer") AND Python AND FastAPI AND (PostgreSQL OR SQL) AND (AWS OR Docker)'], ['Naukri.com - Plain Non-Boolean Version', 'Senior Backend Engineer Python FastAPI PostgreSQL AWS Docker 5 years Bengaluru']].map(([title, value]) => <div className="search-card" key={title}><h4>{title}</h4><pre><code>{value}</code></pre></div>)}</section>,
  ][step - 1];

  if (!isAuthenticated) {
    return <div className="recine-shell"><header className="recine-header"><div className="brand"><div className="brand-mark"><Sparkles size={18} /></div><div><strong>RECINE AI</strong><span>Enterprise talent acquisition</span></div></div></header><main className="recine-login"><div className="login-card"><span className="eyebrow">Enterprise authentication</span><h1>{authMode === 'sign-in' ? 'Sign in to Recine AI' : 'Create your recruiter account'}</h1><p>{authMode === 'sign-in' ? 'Start a governed, evidence-first recruitment pipeline for your next hiring brief.' : 'Create a local demo recruiter account for this standalone workspace.'}</p><div className="login-status"><ShieldCheck size={18} /><span>TA Enterprise Suite is ready</span></div><form onSubmit={handleAuthentication} className="auth-form">{authMode === 'sign-up' && <label>Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Senior Recruiter" autoComplete="name" /></label>}<label>Work email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="recruiter@company.com" autoComplete="email" required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Minimum 8 characters" autoComplete={authMode === 'sign-in' ? 'current-password' : 'new-password'} required /></label>{authError && <div className="auth-error">{authError}</div>}<button className="primary-button" type="submit">{authMode === 'sign-in' ? 'Sign in' : 'Create account'} <ChevronRight size={16} /></button></form><button className="auth-switch" onClick={() => { setAuthMode(authMode === 'sign-in' ? 'sign-up' : 'sign-in'); setAuthError(null); }}>{authMode === 'sign-in' ? 'New recruiter? Create an account' : 'Already registered? Sign in'}</button></div></main></div>;
  }

  return <div className="recine-shell"><header className="recine-header"><div className="brand"><div className="brand-mark"><Sparkles size={18} /></div><div><strong>RECINE AI</strong><span>Enterprise talent acquisition</span></div></div><div className="header-actions"><span className="secure-badge"><ShieldCheck size={15} /> Fairness guardrail on</span><span className="user-chip">{user?.full_name || 'Senior Recruiter'}</span><button className="icon-button" title="Sign out" onClick={logout}><LogOut size={17} /></button></div></header><div className="recine-layout"><aside className="stepper"><div className="stepper-intro"><span className="eyebrow">Recine AI pipeline</span><h1>Hire with signal.</h1><p>A strict seven-step trail from job description to shortlist.</p></div><nav>{steps.map((label, index) => <button key={label} className={`step-item ${step === index + 1 ? 'active' : ''} ${step > index + 1 ? 'done' : ''}`} onClick={() => go(index + 1)}><span className="step-number">{step > index + 1 ? <Check size={14} /> : `0${index + 1}`}</span><span>{label}</span></button>)}</nav><div className="privacy-note"><LockKeyhole size={15} /><span>Fair ranking excludes name, gender, age, photo, and marital status.</span></div></aside><main className="workspace">{header}{content}</main></div></div>;
}
