import React from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import ZelthyLandingPageBgImg from '/img/zelthy_landing_pg_bg.jpg';

export default function Home() {
  const {siteConfig} = useDocusaurusContext();

  return (
    <Layout
      title={`Login Package`}
      description="Login Package">
      <main>
      <iframe
        style={{height: '100vh'}}
        title="Embedded Content"
        width="100%"
        height="100vh"
        src="http://zelthy3-docs-pkg-zelthy3-login.s3-website.ap-south-1.amazonaws.com/docs/documentation/introduction/"
        frameBorder="0"
        allowFullScreen
      ></iframe>
      </main>
    </Layout>
  );
}
