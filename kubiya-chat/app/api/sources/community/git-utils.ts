import { execSync } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

export const REPO_URL = 'https://github.com/kubiyabot/community-tools.git';
export const REPO_PATH = path.join(os.tmpdir(), 'kubiya-community-tools');
const LOCK_FILE = path.join(os.tmpdir(), 'kubiya-community-tools.lock');

export async function acquireLock(): Promise<boolean> {
  try {
    await fs.writeFile(LOCK_FILE, process.pid.toString(), { flag: 'wx' });
    return true;
  } catch (error) {
    try {
      const pid = parseInt(await fs.readFile(LOCK_FILE, 'utf-8'));
      try {
        process.kill(pid, 0);
        return false;
      } catch {
        await fs.unlink(LOCK_FILE);
        return await acquireLock();
      }
    } catch {
      return await acquireLock();
    }
  }
}

export async function releaseLock() {
  try {
    await fs.unlink(LOCK_FILE);
  } catch (error) {
    console.warn('Failed to remove lock file:', error);
  }
}

export async function updateRepo(): Promise<void> {
  const exists = await fs.access(REPO_PATH).then(() => true).catch(() => false);
  
  if (exists) {
    try {
      console.log('Checking for community tools updates...');
      
      // First ensure we're in a clean state
      try {
        execSync('git reset --hard HEAD', { 
          cwd: REPO_PATH,
          stdio: 'pipe',
          encoding: 'utf-8'
        });
      } catch (error) {
        console.log('Failed to reset repository, will re-clone:', error);
        throw error; // This will trigger the catch block below
      }

      // Fetch updates
      execSync('git fetch origin', { 
        cwd: REPO_PATH,
        stdio: 'pipe',
        encoding: 'utf-8'
      });

      // Check if we're behind origin
      const statusOutput = execSync('git status -uno', { 
        cwd: REPO_PATH,
        stdio: 'pipe',
        encoding: 'utf-8'
      });

      if (statusOutput.includes('behind')) {
        console.log('Updates found, pulling changes...');
        execSync('git pull origin main --ff-only', { 
          cwd: REPO_PATH,
          stdio: 'pipe',
          encoding: 'utf-8'
        });
        console.log('Successfully pulled updates');
      } else {
        console.log('Repository is up to date');
      }
    } catch (error) {
      console.log('Update failed, re-cloning repo...', error);
      try {
        await fs.rm(REPO_PATH, { recursive: true, force: true });
        execSync(`git clone ${REPO_URL} ${REPO_PATH} --depth 1`, {
          stdio: 'pipe',
          encoding: 'utf-8'
        });
        console.log('Successfully re-cloned repository');
      } catch (cloneError) {
        console.error('Failed to clone repository:', cloneError);
        throw cloneError;
      }
    }
  } else {
    console.log('Cloning community tools repo...');
    try {
      execSync(`git clone ${REPO_URL} ${REPO_PATH} --depth 1`, {
        stdio: 'pipe',
        encoding: 'utf-8'
      });
      console.log('Successfully cloned repository');
    } catch (cloneError) {
      console.error('Failed to clone repository:', cloneError);
      throw cloneError;
    }
  }
} 