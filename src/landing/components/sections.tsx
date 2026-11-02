import {
  FAQ, FEATURES, LOGIN_URL, MODES, NAV_LINKS, SIGNUP_URL, STEPS, TRUST,
} from './content'

export const SECTION_IDS = ['how-it-works', 'features', 'trust', 'faq']

const container = 'mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8'

export function SkipLink() {
  return (
    <a
      href="#main"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-white focus:px-4 focus:py-2 focus:text-selph-violet"
    >
      Skip to content
    </a>
  )
}

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav aria-label="Main" className={`${container} flex h-16 items-center justify-between`}>
        <a href="#top" className="font-display text-xl font-extrabold text-selph-title">
          SELPH
        </a>
        <ul className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="text-sm font-medium text-selph-muted hover:text-selph-title">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-3">
          <a href={LOGIN_URL} className="text-sm font-medium text-selph-muted hover:text-selph-title">
            Log in
          </a>
          <a
            href={SIGNUP_URL}
            className="rounded-lg bg-selph-violet px-4 py-2 text-sm font-semibold text-white hover:bg-selph-purple"
          >
            Get started
          </a>
        </div>
      </nav>
    </header>
  )
}

export function Hero() {
  return (
    <section id="top" className="bg-gradient-to-b from-selph-cloud to-white">
      <div className={`${container} py-20 text-center sm:py-28`}>
        <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-selph-violet">Your digital twin</p>
        <h1 className="font-display text-4xl font-extrabold leading-tight text-selph-title sm:text-6xl">
          Replies that sound like you.
          <br />
          <span className="gradient-text">Sent only when you say so.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-selph-muted sm:text-xl">
          SELPH learns your voice and drafts replies to your Instagram DMs and Gmail. You approve, edit or reject every
          one. Your twin learns from each decision.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href={SIGNUP_URL}
            className="rounded-xl bg-selph-violet px-8 py-3 text-base font-semibold text-white shadow-lg hover:bg-selph-purple"
          >
            Create your twin
          </a>
          <a href="#how-it-works" className="rounded-xl border border-slate-300 px-8 py-3 text-base font-semibold text-selph-title hover:bg-slate-50">
            See how it works
          </a>
        </div>
        <p className="mt-4 text-sm text-selph-muted">No AI provider key needed to try it.</p>
      </div>
    </section>
  )
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className={`${container} py-20`} aria-labelledby="how-heading">
      <h2 id="how-heading" className="text-center font-display text-3xl font-extrabold text-selph-title sm:text-4xl">
        How it works
      </h2>
      <ol className="mt-12 grid gap-8 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.title} className="rounded-2xl border border-slate-200 p-6">
            <span
              aria-hidden="true"
              className="flex h-10 w-10 items-center justify-center rounded-full bg-selph-cloud font-display text-lg font-bold text-selph-violet"
            >
              {i + 1}
            </span>
            <h3 className="mt-4 font-display text-xl font-bold text-selph-title">{s.title}</h3>
            <p className="mt-2 leading-relaxed text-selph-muted">{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

export function Features() {
  return (
    <section id="features" className="bg-selph-mist py-20" aria-labelledby="features-heading">
      <div className={container}>
        <h2 id="features-heading" className="text-center font-display text-3xl font-extrabold text-selph-title sm:text-4xl">
          Built for people with too many messages
        </h2>
        <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <li key={f.id} id={`feature-${f.id}`} className="rounded-2xl bg-white p-6 shadow-sm">
              <h3 className="font-display text-lg font-bold text-selph-title">{f.title}</h3>
              <p className="mt-2 leading-relaxed text-selph-muted">{f.body}</p>
            </li>
          ))}
        </ul>

        <h3 className="mt-16 text-center font-display text-2xl font-bold text-selph-title">Two ways to show up</h3>
        <ul className="mx-auto mt-8 grid max-w-3xl gap-6 md:grid-cols-2">
          {MODES.map((m) => (
            <li key={m.name} className="rounded-2xl border border-slate-200 bg-white p-6">
              <p className="font-display text-lg font-bold text-selph-title">{m.name}</p>
              <p className="text-sm font-medium text-selph-violet">{m.tagline}</p>
              <p className="mt-2 leading-relaxed text-selph-muted">{m.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

export function Trust() {
  return (
    <section id="trust" className={`${container} py-20`} aria-labelledby="trust-heading">
      <h2 id="trust-heading" className="text-center font-display text-3xl font-extrabold text-selph-title sm:text-4xl">
        Safety is not a setting
      </h2>
      <p className="mx-auto mt-4 max-w-2xl text-center text-lg text-selph-muted">
        A twin that speaks for you has to earn trust. These rules are built in.
      </p>
      <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {TRUST.map((t) => (
          <li key={t.title} className="rounded-2xl border border-slate-200 p-6">
            <h3 className="font-display text-lg font-bold text-selph-title">{t.title}</h3>
            <p className="mt-2 leading-relaxed text-selph-muted">{t.body}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function Faq() {
  return (
    <section id="faq" className="bg-selph-cloud py-20" aria-labelledby="faq-heading">
      <div className={`${container} max-w-3xl`}>
        <h2 id="faq-heading" className="text-center font-display text-3xl font-extrabold text-selph-title sm:text-4xl">
          Questions
        </h2>
        <div className="mt-10 space-y-4">
          {FAQ.map((item) => (
            <details key={item.q} className="group rounded-xl bg-white p-5 shadow-sm">
              <summary className="cursor-pointer list-none font-display text-lg font-semibold text-selph-title">
                {item.q}
              </summary>
              <p className="mt-3 leading-relaxed text-selph-muted">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

export function FinalCta() {
  return (
    <section className={`${container} py-20 text-center`}>
      <h2 className="font-display text-3xl font-extrabold text-selph-title sm:text-4xl">
        Spend seconds on messages, not hours.
      </h2>
      <p className="mx-auto mt-4 max-w-xl text-lg text-selph-muted">
        Set up your twin in a few minutes and watch it draft its first reply.
      </p>
      <a
        href={SIGNUP_URL}
        className="mt-8 inline-block rounded-xl bg-selph-violet px-8 py-3 text-base font-semibold text-white shadow-lg hover:bg-selph-purple"
      >
        Create your twin
      </a>
    </section>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-slate-200 py-10">
      <div className={`${container} flex flex-col items-center justify-between gap-4 text-sm text-selph-muted sm:flex-row`}>
        <p>© {new Date().getFullYear()} SELPH. All rights reserved.</p>
        <ul className="flex gap-6">
          {NAV_LINKS.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="hover:text-selph-title">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  )
}
