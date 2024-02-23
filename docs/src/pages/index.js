import React, { useEffect } from "react";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import ZelthyLandingPageBgImg from "/img/zelthy_landing_pg_bg.jpg";

export default function Home() {
  const { siteConfig } = useDocusaurusContext();

  useEffect(() => {
    window.location.href = "/docs/docs/documentation/introduction/";
  }, []);

  return (
    <Layout title={`Zelthy Docs`} description="Zelthy Docs">
      <main>
        {/* <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <img src={ZelthyLandingPageBgImg} />
      </div> */}
      </main>
    </Layout>
  );
}
