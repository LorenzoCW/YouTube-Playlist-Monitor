import Plot from 'react-plotly.js';

interface ChartProps {
  data: { x: number; y: number }[];
  title: string;
  color: string;
}

const Chart: React.FC<ChartProps> = ({ data, title, color }) => {
  const x = data.map(pt => pt.x);
  const y = data.map(pt => pt.y);

  return (
    <Plot
      data={[{
        x,
        y,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color },
        name: title,
        hovertemplate: '%{x|%d/%m} - %{y}<extra></extra>'
      }]}
      layout={{
        plot_bgcolor: '#111111',
        paper_bgcolor: '#111111',
        title: {
          text: title,
          font: { color: '#6e6e6e' },
        },
        xaxis: {
          title: 'Data',
          color: '#f1f1f1',
          tickformat: '%d/%m'
        },
        yaxis: {
          title,
          color: color,
          side: 'right'
        },
        height: 375
      }}
      style={{ width: '100%' }}
    />
  );
};

export default Chart;