/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // static site: deployable to any static host / CDN
  trailingSlash: true,
  images: { unoptimized: true },
}

module.exports = nextConfig
