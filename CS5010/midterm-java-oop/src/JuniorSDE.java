public class JuniorSDE extends EngineerImp {
    private final int linesOfCode;

    public JuniorSDE(String name, double baseSalary, int linesOfCode) {
        super(name, baseSalary);
        this.linesOfCode = linesOfCode;
    }

    @Override
    public void setBonus(Rating rating) {
        double baseBonus = computeBaseBonus();
        double bonusRatio = linesOfCode / 100.0;
        if (rating == Rating.SUPERB) {
            bonusRatio *= 2.0;
        }
        this.bonus = baseBonus * bonusRatio;
    }
}
