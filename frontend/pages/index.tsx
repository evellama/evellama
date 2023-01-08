import Head from 'next/head'
import Image from 'next/image'

import logo from '../public/logo.jpeg'

const IndexPage = () => {
  return (
    <>
      <Head>
        <title>EVE Llama</title>
      </Head>
      <div className="flex flex-col min-h-full pt-16 pb-12">
        <main className="flex flex-col justify-center flex-grow w-full px-4 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="flex justify-center flex-shrink-0">
            <h1 className="sr-only">EVE Llama</h1>
            <Image src={logo} alt="EVE Llama logo" className="inline-flex w-24 h-24 rounded-full ring-primary ring-offset-1 ring-1" />
          </div>
          <div className="py-16">
            <div className="text-center">
              <p className="mt-2 text-4xl font-bold tracking-tight text-primary sm:text-5xl">
                Coming soon.
              </p>
            </div>
          </div>
        </main>
      </div>
    </>
  )
}

export default IndexPage
