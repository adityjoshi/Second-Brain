const http = require('http');

let reqCount = 0;

http.createServer((req, res) => {
  const currentReq = ++reqCount;
  console.log(`👉 Received request ${currentReq} at ${new Date().toISOString()}`);

  // Simulate blocking CPU-heavy task
  const start = Date.now();
  for (let i = 0; i < 1e9; i++) {} // CPU-intensive loop
  const end = Date.now();

  console.log(`✅ Finished request ${currentReq} - Took ${end - start}ms`);

  res.end(`Done with request ${currentReq}\n`);
}).listen(3000, () => {
  console.log('🚀 Server listening on port 3000');
});

