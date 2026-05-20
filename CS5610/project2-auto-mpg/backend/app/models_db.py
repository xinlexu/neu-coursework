from sqlalchemy import Column, Integer, Text, JSON, DateTime, func, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True)
    model_type = Column(Text, nullable=False)
    params = Column(JSON, nullable=False)
    metrics = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    predictions = relationship("Prediction", back_populates="experiment")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="SET NULL"))
    input = Column(JSON, nullable=False)
    output = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    experiment = relationship("Experiment", back_populates="predictions")
