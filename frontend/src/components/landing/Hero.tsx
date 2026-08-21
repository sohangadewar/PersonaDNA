import HeroBackground from "./HeroBackground";
import HeroContent from "./HeroContent";
import HeroStats from "./HeroStats";

const Hero = () => {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#09090B]">
      <HeroBackground />

      <div className="relative z-10">
        <HeroContent />
        <HeroStats />
      </div>
    </section>
  );
};

export default Hero;