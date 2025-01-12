"use client";

interface KubernetesResourceProps {
  kind: string;
  items: {
    metadata: {
      name: string;
      namespace: string;
    };
    spec?: {
      replicas?: number;
    };
    status?: {
      availableReplicas?: number;
      readyReplicas?: number;
    };
  }[];
}

export function KubernetesResource({ kind, items }: KubernetesResourceProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 my-2">
      <h3 className="text-lg font-semibold mb-2">{kind}</h3>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={index} className="bg-white p-4 rounded-md shadow-sm">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium">{item.metadata.name}</p>
                <p className="text-sm text-gray-500">Namespace: {item.metadata.namespace}</p>
              </div>
              {item.spec?.replicas && (
                <div className="text-right">
                  <p className="text-sm">
                    Replicas: {item.status?.readyReplicas || 0}/{item.spec.replicas}
                  </p>
                  <p className="text-sm text-gray-500">
                    Available: {item.status?.availableReplicas || 0}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 