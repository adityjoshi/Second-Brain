const http = require('http');

let reqCount = 0;

http.createServer(async (req, res) => {
  const currentReq = ++reqCount;
  console.log(`👉 Received request ${currentReq} at ${new Date().toISOString()}`);

  // Simulate async I/O operation (non-blocking)
  await new Promise((resolve) => setTimeout(resolve, 2000)); // 2 sec async wait

  console.log(`✅ Finished request ${currentReq} at ${new Date().toISOString()}`);
  res.end(`Done with request ${currentReq}\n`);
}).listen(3000, () => {
  console.log('🚀 Async server listening on port 3000');
});

