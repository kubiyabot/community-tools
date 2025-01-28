import * as React from 'react';

export const AWS: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M18.75 10.5L12 14.25L5.25 10.5M18.75 15L12 18.75L5.25 15M12 5.25L18.75 9L12 12.75L5.25 9L12 5.25Z" />
  </svg>
); 