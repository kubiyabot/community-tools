import { NextResponse } from 'next/server';

export async function PUT(
  request: Request,
  { params }: { params: { sourceId: string } }
) {
  try {
    const { sourceId } = params;
    const { dynamic_config } = await request.json();

    const response = await fetch(
      `${process.env.KUBIYA_API_URL}/api/v1/sources/${sourceId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.KUBIYA_API_KEY}`,
        },
        body: JSON.stringify({ dynamic_config }),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to sync source: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error syncing source:', error);
    return NextResponse.json(
      { error: 'Failed to sync source' },
      { status: 500 }
    );
  }
} 