export default function Home() {
  return (
    <div className="card">
      <h2>Overview</h2>
      <p>This app shows a simple regression workflow on an offline Auto MPG dataset.</p>
      <ol>
        <li>Go to <b>Train</b>, choose a model, click <b>Train</b>. You will get an <code>experiment_id</code>.</li>
        <li>Go to <b>Estimate</b>, paste the <code>experiment_id</code>, fill all fields, click <b>Predict</b>.</li>
        <li>Training runs and predictions are saved to PostgreSQL (<code>experiments</code>, <code>predictions</code>).</li>
      </ol>

      <div style={{marginTop:16}}>
        <h3>Glossary</h3>
        <ul>
          <li><b>MPG</b>: miles per gallon. Higher is more fuel-efficient.</li>
          <li><b>MSE</b>: mean squared error on a held-out set (lower is better).</li>
          <li><b>MAE</b>: mean absolute error on a held-out set (lower is better).</li>
          <li><b>R²</b>: how much variance is explained by the model (closer to 1 is better).</li>
          <li><b>experiment_id</b>: an ID for a trained model. Use it on the Estimate page.</li>
          <li><b>Features</b>: cylinders, displacement (ci), horsepower (hp), weight (lb),
            acceleration (0–60s), model_year (70=1970 ... 82=1982), origin (1=US,2=Europe,3=Japan).</li>
          <li><b>Interval</b>: an empirical band around the prediction based on validation residuals.</li>
        </ul>
      </div>

      {/* Optional screenshot if provided as /project2.png */}
      <img className="hero" src="/project2.png" alt="Project screenshot" />
    </div>
  )
}
