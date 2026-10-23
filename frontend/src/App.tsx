import { NavLink, Route, Routes } from "react-router-dom";
import EditarInspecaoPage from "./pages/EditarInspecaoPage";
import InspecaoDetalhePage from "./pages/InspecaoDetalhePage";
import InspecoesPage from "./pages/InspecoesPage";
import NovaInspecaoPage from "./pages/NovaInspecaoPage";
import PainelPage from "./pages/PainelPage";

export default function App() {
  return (
    <>
      <header className="topo">
        <span className="marca">Inspeções Simuladas</span>
        <nav aria-label="Principal">
          <NavLink to="/" end>Painel</NavLink>
          <NavLink to="/inspecoes" end>Inspeções</NavLink>
          <NavLink to="/inspecoes/nova">Nova inspeção</NavLink>
        </nav>
        <span className="aviso-ficticio">Dados fictícios</span>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<PainelPage />} />
          <Route path="/inspecoes" element={<InspecoesPage />} />
          <Route path="/inspecoes/nova" element={<NovaInspecaoPage />} />
          <Route path="/inspecoes/:id" element={<InspecaoDetalhePage />} />
          <Route path="/inspecoes/:id/editar" element={<EditarInspecaoPage />} />
          <Route path="*" element={<p className="estado">Página não encontrada.</p>} />
        </Routes>
      </main>
    </>
  );
}
