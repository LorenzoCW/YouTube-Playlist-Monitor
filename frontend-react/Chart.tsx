import Plot from 'react-plotly.js';
import { Layout } from 'plotly.js';

interface ChartProps {
  data: { x: number; y: number }[];
  chartTitle: string;
  color: string;
}

const Chart: React.FC<ChartProps> = ({ data, chartTitle, color }) => {
  const x = data.map(pt => pt.x);
  const y = data.map(pt => pt.y);

  const layout: Partial<Layout> = {
    plot_bgcolor: '#111111',
    paper_bgcolor: '#111111',
    title: {
      text: chartTitle,
      font: { color: '#6e6e6e' },
    },
    xaxis: {
      title: {
        text: 'Data',
        font: { color: '#f1f1f1' }
      },
      color: '#f1f1f1',
      tickformat: '%d/%m'
    },
    yaxis: {
      title: {
        text: chartTitle,
        font: { color }
      },
      color: color,
      side: 'right'
    },
    height: 365
  };

  return (
    <Plot
      data={[{
        x,
        y,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color },
        name: chartTitle,
        hovertemplate: '%{x|%d/%m} - %{y}<extra></extra>'
      }]}
      layout={layout}
      style={{ width: '100%' }}
    />
  );
};

export default Chart;