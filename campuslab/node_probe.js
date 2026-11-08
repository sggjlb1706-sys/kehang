'use strict';
// Fixed probes only. No install, network fetch, PATH npm, or user-supplied code.
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const actual = fs.realpathSync(process.execPath);
const cli = path.join(path.dirname(actual), 'node_modules', 'npm', 'bin', 'npm-cli.js');
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !['NODE_OPTIONS', 'NODE_PATH'].includes(key.toUpperCase()) && !key.toLowerCase().startsWith('npm_config_')));
const options = {encoding:'utf8', timeout:15000, maxBuffer:262144, windowsHide:true, env, cwd:path.dirname(actual)};
const npm = {path:cli, node:null, exists:false, version:null, returncode:null, error:'所选Node目录未找到npm CLI'};
const commands = [];
const npmArgs = [cli, '--version', '--offline', '--ignore-scripts', '--no-update-notifier', '--userconfig=NUL', '--globalconfig=NUL'];
try {
  if (fs.statSync(cli).isFile()) {
    npm.path = fs.realpathSync(cli);
    npm.node = actual;
    npm.exists = true;
    const result = spawnSync(actual, npmArgs, options);
    commands.push([actual, ...npmArgs]);
    npm.returncode = result.status;
    npm.version = result.stdout?.trim() || null;
    npm.error = result.error ? `${result.error.code}: ${result.error.message}` : (result.stderr || '');
  }
} catch (error) {
  if (error.code !== 'ENOENT') {
    npm.exists = null;
    npm.error = `${error.code}: ${error.message}`;
  }
}
const fixedCode = "require('node:assert/strict').equal([1,2,3].map(n=>n*2).join(','),'2,4,6'); console.log('OK')";
const runArgs = ['--input-type=commonjs', '-e', fixedCode];
const run = spawnSync(actual, runArgs, options);
commands.push([actual, ...runArgs]);
const verification = {returncode:run.status, stdout:run.stdout || '',
  error:run.error ? `${run.error.code}: ${run.error.message}` : (run.stderr || '')};
console.log(JSON.stringify({actual, commands, facts:{os:process.platform === 'win32' ? 'Windows' : process.platform,
  node:process.versions.node, npm, verification}}));
