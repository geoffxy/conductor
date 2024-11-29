import logo from './assets/ConductorLogo_Light.png';
import './Header.css';

const Header = () => {
  console.log('Test');
  return <div class="header">
    <div class="header-logo">
      <img src={logo} alt="Conductor Explorer" />
      <span>Conductor Explorer</span>
    </div>
  </div>;
};

export default Header;
