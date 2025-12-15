import { useState, useEffect } from 'react';
import { Campaign, CampaignProgress, campaignApi } from '../lib/campaignApi';

interface UseCampaignProgressProps {
  campaignId: string;
  enabled: boolean;
  interval?: number;
}

export function useCampaignProgress({ campaignId, enabled, interval = 2000 }: UseCampaignProgressProps) {
  const [progress, setProgress] = useState<CampaignProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !campaignId) return;

    let intervalId: NodeJS.Timeout;

    const fetchProgress = async () => {
      try {
        setLoading(true);
        const data = await campaignApi.getCampaignProgress(campaignId);
        setProgress(data);
        setError(null);

        // Stop polling if campaign is completed or failed
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch progress');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchProgress();

    // Set up polling
    intervalId = setInterval(fetchProgress, interval);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [campaignId, enabled, interval]);

  return { progress, loading, error };
}
