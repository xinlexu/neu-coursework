public class SeniorSDE extends EngineerImp {
    private final int numReports;

    public SeniorSDE(String name, double baseSalary, int numReports) {
        super(name, baseSalary);
        this.numReports = numReports;
    }

    @Override
    public void setBonus(Rating rating) {
        double baseBonus = computeBaseBonus();
        double bonusRatio = numReports / 5.0;
        this.bonus = baseBonus * bonusRatio;
    }
}
