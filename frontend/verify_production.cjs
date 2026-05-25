const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

let mockFound = false;
let issues = [];

function scanDirectory(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      scanDirectory(fullPath);
    } else if (stat.isFile() && (fullPath.endsWith('.js') || fullPath.endsWith('.jsx'))) {
      const content = fs.readFileSync(fullPath, 'utf8');
      if (content.includes('mockData') || content.includes('mockEvents') || content.includes('MOCK_')) {
        mockFound = true;
        issues.push(`Mock data reference found in: ${fullPath}`);
      }
    }
  }
}

scanDirectory(srcDir);

if (mockFound) {
  console.error('❌ Frontend Verification Failed: Mock data placeholders detected!');
  issues.forEach(i => console.error(i));
  process.exit(1);
} else {
  console.log('✅ Frontend Verification Passed: No mock placeholders found.');
  process.exit(0);
}
