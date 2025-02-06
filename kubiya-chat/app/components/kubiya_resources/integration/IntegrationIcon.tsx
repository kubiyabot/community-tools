"use client";

import { Database, Globe, Settings, GitMerge } from 'lucide-react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import type { IntegrationType } from '@/app/types/integration';

interface IntegrationIconProps {
  type?: IntegrationType;
  name?: string;
  className?: string;
}

// Helper function to check if a string includes any of the given terms
function includesAny(str: string, terms: string[]): boolean {
  return terms.some(term => str.includes(term));
}

function getIconUrl(type: string, name: string): string | null {
  const normalizedType = type.toLowerCase();
  const normalizedName = name.toLowerCase();

  // Cloud Providers
  if (includesAny(normalizedType, ['aws'])) {
    return 'https://static-00.iconduck.com/assets.00/aws-icon-2048x1224-tyr5ef11.png';
  }

  // Version Control
  if (includesAny(normalizedType, ['github'])) {
    return 'https://cdn-icons-png.flaticon.com/512/25/25231.png';
  }
  if (includesAny(normalizedType, ['gitlab'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/gitlab/gitlab-original.svg';
  }
  if (includesAny(normalizedType, ['bitbucket'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/bitbucket/bitbucket-original.svg';
  }

  // Collaboration
  if (includesAny(normalizedType, ['jira'])) {
    return 'https://static-00.iconduck.com/assets.00/jira-icon-2048x2048-nmec2job.png';
  }
  if (includesAny(normalizedType, ['slack'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/slack/slack-original.svg';
  }
  if (includesAny(normalizedType, ['confluence'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/confluence/confluence-original.svg';
  }

  // Databases
  if (includesAny(normalizedName, ['postgres', 'postgresql'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original.svg';
  }
  if (includesAny(normalizedName, ['mysql'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/mysql/mysql-original.svg';
  }
  if (includesAny(normalizedName, ['mongodb'])) {
    return 'https://raw.githubusercontent.com/devicons/devicon/master/icons/mongodb/mongodb-original.svg';
  }

  return null;
}

export function IntegrationIcon({ type = 'generic', name = '', className }: IntegrationIconProps) {
  const iconUrl = getIconUrl(type, name);

  if (!iconUrl) {
    if (type === 'generic') {
      return <Settings className={cn('h-6 w-6 text-[#7C3AED]', className)} />;
    }
    if (includesAny(type, ['github', 'gitlab', 'bitbucket'])) {
      return <GitMerge className={cn('h-6 w-6 text-[#7C3AED]', className)} />;
    }
    if (includesAny(name, ['database', 'sql', 'db'])) {
      return <Database className={cn('h-6 w-6 text-[#7C3AED]', className)} />;
    }
    return <Globe className={cn('h-6 w-6 text-[#7C3AED]', className)} />;
  }

  return (
    <div className={cn('relative h-6 w-6', className)}>
      <Image
        src={iconUrl}
        alt={`${type} icon`}
        fill
        className="object-contain"
      />
    </div>
  );
} 