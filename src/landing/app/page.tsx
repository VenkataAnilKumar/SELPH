import { Faq, Features, FinalCta, Footer, Hero, HowItWorks, Nav, SkipLink, Trust } from '@/components/sections'

export default function Home() {
  return (
    <>
      <SkipLink />
      <Nav />
      <main id="main">
        <Hero />
        <HowItWorks />
        <Features />
        <Trust />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
    </>
  )
}
