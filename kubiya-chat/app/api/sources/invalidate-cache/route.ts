import { NextResponse } from 'next/server';
import { revalidatePath } from 'next/cache';

export async function POST() {
  try {
    // Revalidate the sources API routes
    revalidatePath('/api/sources');
    revalidatePath('/api/teammates/[id]/sources');
    
    return NextResponse.json({ revalidated: true, now: Date.now() });
  } catch (err) {
    return NextResponse.json(
      { 
        revalidated: false, 
        now: Date.now(),
        error: err instanceof Error ? err.message : 'Failed to revalidate cache'
      },
      { status: 500 }
    );
  }
} 