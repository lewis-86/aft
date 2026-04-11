// aft/src/github-app/index.js
const { Probot } = require('probot');
const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');

module.exports = async function app(probot) {
  // Load config
  let config = {};
  try {
    const configPath = path.join(__dirname, '../../config/default.yaml');
    config = yaml.load(fs.readFileSync(configPath, 'utf8'));
  } catch (e) {
    // Use defaults
  }

  probot.on('pull_request.opened', async (context) => {
    const pr = context.payload.pull_request;
    const diff = await context.octokit.pulls.get({
      owner: context.payload.repository.owner.login,
      repo: context.payload.repository.name,
      pull_number: pr.number,
    }).then(r => r.data.diff);

    // Forward to Python AFT service via HTTP
    // In production, this would call the AFT backend service
    const comment = `## AFT Analysis\n\nAnalyzing PR #${pr.number}: ${pr.title}...\n\nPlease configure your AFT backend URL to enable AI analysis.`;
    return context.octokit.issues.createComment({
      issue_number: pr.number,
      owner: context.payload.repository.owner.login,
      repo: context.payload.repository.name,
      body: comment,
    });
  });
};