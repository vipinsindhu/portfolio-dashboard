function PlanForm({ onSubmit }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    const formData = {
      amount: parseFloat(e.target.amount.value),
      timeline: e.target.timeline.value,
      existing: e.target.existing.value,
      risk: e.target.risk.value,
    }
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '500px', marginBottom: '20px' }}>
      <div>
        <label htmlFor="amount">Investment Amount ($)</label>
        <input
          type="number"
          id="amount"
          name="amount"
          placeholder="10000"
          min="0"
          step="100"
          required
        />
      </div>

      <div>
        <label>Investment Timeline</label>
        <div className="radio-group">
          <label className="radio-option">
            <input type="radio" name="timeline" value="short" required /> Short-term (0–2 years)
          </label>
          <label className="radio-option">
            <input type="radio" name="timeline" value="medium" required /> Medium-term (2–5 years)
          </label>
          <label className="radio-option">
            <input type="radio" name="timeline" value="long" required /> Long-term (5+ years)
          </label>
        </div>
      </div>

      <div>
        <label>Current Portfolio</label>
        <div className="radio-group">
          <label className="radio-option">
            <input type="radio" name="existing" value="none" required /> Starting fresh
          </label>
          <label className="radio-option">
            <input type="radio" name="existing" value="small" required /> Already have &lt;$50k
          </label>
          <label className="radio-option">
            <input type="radio" name="existing" value="medium" required /> Have $50k–$500k
          </label>
          <label className="radio-option">
            <input type="radio" name="existing" value="large" required /> Have &gt;$500k
          </label>
        </div>
      </div>

      <div>
        <label>Risk Tolerance</label>
        <div className="radio-group">
          <label className="radio-option">
            <input type="radio" name="risk" value="conservative" required /> Conservative (low volatility)
          </label>
          <label className="radio-option">
            <input type="radio" name="risk" value="moderate" required /> Moderate (balanced)
          </label>
          <label className="radio-option">
            <input type="radio" name="risk" value="aggressive" required /> Aggressive (high growth)
          </label>
        </div>
      </div>

      <button type="submit">Generate Recommendation</button>
    </form>
  )
}

export default PlanForm
