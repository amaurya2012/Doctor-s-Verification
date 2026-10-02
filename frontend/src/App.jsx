import { Routes, Route } from "react-router-dom";
import Shell from "./components/Shell";
import RequireAuth from "./components/RequireAuth";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Feed from "./pages/Feed";
import DoctorSearch from "./pages/DoctorSearch";
import DoctorProfile from "./pages/DoctorProfile";
import MyDoctorProfile from "./pages/MyDoctorProfile";
import UserProfile from "./pages/UserProfile";
import SOS from "./pages/SOS";
import Notifications from "./pages/Notifications";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route path="/" element={<Feed />} />
        <Route path="/doctors" element={<DoctorSearch />} />
        <Route path="/doctors/:id" element={<DoctorProfile />} />
        <Route path="/u/:id" element={<UserProfile />} />

        <Route
          path="/my-profile"
          element={
            <RequireAuth>
              <MyDoctorProfile />
            </RequireAuth>
          }
        />
        <Route
          path="/sos"
          element={
            <RequireAuth>
              <SOS />
            </RequireAuth>
          }
        />
        <Route
          path="/notifications"
          element={
            <RequireAuth>
              <Notifications />
            </RequireAuth>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireAuth adminOnly>
              <Admin />
            </RequireAuth>
          }
        />
      </Routes>
    </Shell>
  );
}
