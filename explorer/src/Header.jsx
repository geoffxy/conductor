import logo from "./assets/ConductorLogo_Light.png";
import "./Header.css";

const Header = () => {
  return (
    <div className="header">
      <div className="header-logo">
        <img src={logo} alt="Conductor Explorer" />
        <span>Conductor Explorer</span>
      </div>
    </div>
  );
};

export default Header;
