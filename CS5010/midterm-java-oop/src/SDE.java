public class SDE extends EngineerImp {
    private final int linesOfCode;
    private final int numDesignDocs;

    public SDE(String name, double baseSalary, int linesOfCode, int numDesignDocs) {
        super(name, baseSalary);
        this.linesOfCode = linesOfCode;
        this.numDesignDocs = numDesignDocs;
    }

    @Override
    public void setBonus(Rating rating) {
        double baseBonus = computeBaseBonus();
        double bonusRatio = linesOfCode / 80.0 + numDesignDocs / 5.0;
        if (rating == Rating.EXCEED_EXPECTATION) {
            bonusRatio *= 1.2;
        } else if (rating == Rating.SUPERB) {
            bonusRatio *= 1.7;
        }
        this.bonus = baseBonus * bonusRatio;
    }
}
