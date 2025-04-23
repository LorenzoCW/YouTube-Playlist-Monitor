import { useEffect, useState } from 'react';
import { doc, getDoc } from 'firebase/firestore';
import Chart from './Chart';
import './App.css';
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_API_KEY,
  authDomain: process.env.REACT_APP_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_PROJECT_ID,
  storageBucket: process.env.REACT_APP_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

interface VideoChanges {
  current_videos: number;
  change_indicator: string;
  current_minutes: number;
  current_hours: number;
  last_day_difference: number;
  last_week_difference: number;
  last_week_added: number;
  last_week_removed: number;
  last_week_average_change: number;
  last_month_difference: number;
  last_month_added: number;
  last_month_removed: number;
  last_month_average_change: number;
  total_difference: number;
  total_added: number;
  total_removed: number;
  total_average_change: number;
}

interface MinuteChanges {
  current_minutes: number;
  current_hours: number;
  change_indicator: string;
  minutes_per_video: number;
  last_day_difference: number;
  last_week_difference: number;
  last_week_added: number;
  last_week_removed: number;
  last_week_average_change: number;
  last_month_difference: number;
  last_month_added: number;
  last_month_removed: number;
  last_month_average_change: number;
  total_difference: number;
  total_added: number;
  total_removed: number;
  total_average_change: number;
}

interface Status {
  success: boolean;
  final_result_timestamp: string;
  final_result: string;
}

function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [videoPoints, setVideoPoints] = useState<any[]>([]);
  const [minutePoints, setMinutePoints] = useState<any[]>([]);
  const [videoChanges, setVideoChanges] = useState<VideoChanges | null>(null);
  const [minuteChanges, setMinuteChanges] = useState<MinuteChanges | null>(null);

  useEffect(() => {
    async function loadData() {
      // Carregar status
      const statusRef = doc(db, 'status', 'playlist_status');
      const statusSnap = await getDoc(statusRef);
      if (statusSnap.exists()) setStatus(statusSnap.data() as Status);

      // Carregar pontos
      const pointsRef = doc(db, 'parsed_data', 'points_array');
      const pointsSnap = await getDoc(pointsRef);
      if (pointsSnap.exists()) {
        const { month_data } = pointsSnap.data();
        setVideoPoints(month_data.video_count_points || []);
        setMinutePoints(month_data.total_minutes_points || []);
      }

      // Carregar cálculos
      const calcsRef = doc(db, 'parsed_data', 'calcs');
      const calcsSnap = await getDoc(calcsRef);
      if (calcsSnap.exists()) {
        const data = calcsSnap.data();
        setVideoChanges(data.video_changes || null);
        setMinuteChanges(data.minute_changes || null);
      }
    }
    loadData();
  }, []);

  function formatChange(qty: number | null, suffix = '', indicator = '') {
    if (qty == null) return null;
    const sign = qty > 0 ? '+' : qty < 0 ? '-' : '';
    const abs = Math.abs(qty);
    return `${indicator === '' ? sign : indicator} ${abs}${suffix}`;
  }

  return (
    <div className="container">
      <header className="box1">
        <h1 className="title">Youtube Playlist Monitor</h1>
        <p>
          {formatChange(videoChanges?.current_videos ?? 0, ' vídeos', videoChanges?.change_indicator ?? '')}
          {(videoChanges?.current_minutes || videoChanges?.current_hours) && ' | '}
          {formatChange(videoChanges?.current_hours ?? 0, 'h :', minuteChanges?.change_indicator ?? '')}{formatChange(videoChanges?.current_minutes ?? 0, 'm', ' ')}
        </p>
        <p>Média de minutos por vídeo: {formatChange(minuteChanges?.minutes_per_video ?? 0, 'm', ' ')}</p>
        {status?.success === false && (
          <h4 className="status">
            {status.final_result_timestamp} - {status.final_result}
          </h4>
        )}
      </header>

      <section className="box2">
        <div className="item">
          <h2>Mudanças</h2>
          <h3>Ontem</h3>
          <table className="tabbed-table">
            <tbody>
              <tr>
                <td>Diferença:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_day_difference ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_day_difference ?? 0, 'm')}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="item">
          <h3>Semana anterior</h3>
          <table className="tabbed-table">
            <tbody>
              <tr>
                <td>Diferença:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_week_difference ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_week_difference ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Adicionados:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_week_added ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_week_added ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Removidos:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_week_removed ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_week_removed ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Média:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_week_average_change ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_week_average_change ?? 0, 'm')}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="item">
          <h3>Mês anterior</h3>
          <table className="tabbed-table">
            <tbody>
              <tr>
                <td>Diferença:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_month_difference ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_month_difference ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Adicionados:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_month_added ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_month_added ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Removidos:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_month_removed ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_month_removed ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Média:</td>
                <td className="tabbed">{formatChange(videoChanges?.last_month_average_change ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.last_month_average_change ?? 0, 'm')}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="item">
          <h3>Começo</h3>
          <table className="tabbed-table">
            <tbody>
              <tr>
                <td>Diferença:</td>
                <td className="tabbed">{formatChange(videoChanges?.total_difference ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.total_difference ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Adicionados:</td>
                <td className="tabbed">{formatChange(videoChanges?.total_added ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.total_added ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Removidos:</td>
                <td className="tabbed">{formatChange(videoChanges?.total_removed ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.total_removed ?? 0, 'm')}</td>
              </tr>
              <tr>
                <td>Média:</td>
                <td className="tabbed">{formatChange(videoChanges?.total_average_change ?? 0)}</td>
                <td className="tabbed">{formatChange(minuteChanges?.total_average_change ?? 0, 'm')}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="graphs">
        <Chart data={videoPoints} title="Vídeos" color="firebrick" />
        <Chart data={minutePoints} title="Minutos" color="dodgerblue" />
      </section>
    </div>
  );
}

export default App;
