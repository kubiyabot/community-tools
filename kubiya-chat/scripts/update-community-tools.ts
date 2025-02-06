import { acquireLock, releaseLock, updateRepo } from '../app/api/sources/community/git-utils';

async function updateCommunityTools() {
  if (!await acquireLock()) {
    console.log('Another update is in progress, skipping...');
    return;
  }

  try {
    await updateRepo();
    console.log('Done!');
  } catch (error) {
    console.error('Failed to update community tools:', error);
    process.exit(1);
  } finally {
    await releaseLock();
  }
}

updateCommunityTools(); 