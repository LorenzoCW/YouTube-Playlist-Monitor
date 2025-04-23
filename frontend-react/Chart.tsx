import Plot from 'react-plotly.js';

interface ChartProps {
  data: { x: number; y: number }[];
  title: string;
  color: string;
}

// export default function Chart({ data, title, color }) {
const Chart: React.FC<ChartProps> = ({ data, title, color }) => {
  const x = data.map(pt => pt.x);
  const y = data.map(pt => pt.y);
  const latest = y.length ? y[y.length - 1] : 0;

  return (
    <Plot
      data={[{
        x,
        y,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color },
        name: `${title}: ${latest}`
      }]}
      layout={{
        plot_bgcolor: '#111111',
        paper_bgcolor: '#111111',
        title: {
          text: title,
          font: { color: '#f1f1f1' },
        },
        xaxis: { title: 'Data', color: '#f1f1f1' },
        yaxis: { title, color: '#f1f1f1' },
        height: 375
      }}
      style={{ width: '100%' }}
    />
  );
}

export default Chart;