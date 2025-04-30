/**
 * Welcome to Cloudflare Workers! This is a template for a Workers Sites project.
 */

import { getAssetFromKV } from '@cloudflare/kv-asset-handler'

/**
 * The DEBUG flag will do two things:
 * 1. we will skip caching on the edge, which makes it easier to debug
 * 2. we will return an error message on exception in your Response rather than the default 500 page
 */
const DEBUG = false

addEventListener('fetch', event => {
  try {
    event.respondWith(handleEvent(event))
  } catch (e) {
    if (DEBUG) {
      return event.respondWith(
        new Response(e.message || e.toString(), {
          status: 500,
        }),
      )
    }
    event.respondWith(new Response('Internal Error', { status: 500 }))
  }
})

async function handleEvent(event) {
  const url = new URL(event.request.url)
  let options = {}

  // Pass through API requests directly to the Flask application
  if (url.pathname.startsWith('/api/')) {
    // Forward to the Flask app
    return fetch(event.request)
  }

  try {
    // Try to serve static assets
    const page = await getAssetFromKV(event, options)
    return page
  } catch (e) {
    // If not a static asset, forward to the Flask app
    return fetch(event.request)
  }
}