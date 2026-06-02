import { useEffect, useRef } from 'react'
import { Chart } from 'chart.js/auto'

function HealthGauge({ score, label, color }) {
  const canvasRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!canvasRef.current) return

    if (chartRef.current) {
      chartRef.current.destroy()
    }

    const ctx = canvasRef.current.getContext('2d')
    chartRef.current = new Chart(ctx, {
      type: 'doughnut',
      data: {
        datasets: [
          {
            data: [score, 100 - score],
            backgroundColor: [color, 'rgba(255, 255, 255, 0.08)'],
            borderColor: 'var(--bg)',
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        circumference: 180,
        rotation: -90,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            enabled: false,
          },
        },
      },
    })

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
      }
    }
  }, [score, color])

  return (
    <div className="chart-card">
      <div className="chart-card-title">Market Health Score</div>
      <div className="chart-card-subtitle" style={{ color }}>
        {label} ({score}%)
      </div>
      <div style={{ height: '120px', display: 'flex', justifyContent: 'center' }}>
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  )
}

export default HealthGauge
