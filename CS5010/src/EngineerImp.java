public abstract class EngineerImp implements Engineer {
    protected String name;
    protected double baseSalary;
    protected double bonus;

    public EngineerImp(String name, double baseSalary) {
        this.name = name;
        this.baseSalary = baseSalary;
        this.bonus = 0;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public double getBonus() {
        return bonus;
    }

    protected double computeBaseBonus() {
        double baseBonus = this.baseSalary;
        baseBonus += pullDepartmentProfit();
        baseBonus += pullNASDQIndex();
        baseBonus += pullManagerMood();
        baseBonus += pullCPI();
        return baseBonus;
    }

    @Override
    public abstract void setBonus(Rating rating);

    @Override
    public int compareTo(Engineer other) {
        return this.name.compareTo(other.getName());
    }
}
