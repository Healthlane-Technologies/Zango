import React, { useState, useEffect } from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import ZelthyLandingPageBgImg from '/img/zelthy_landing_pg_bg.jpg';

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  const [isLoading, setIsLoading] = useState(true); 
  const [hasError, setHasError] = useState(false); 


  const handleIframeLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };


  const handleIframeError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  return (
    <Layout title={`Login Package`} description="Login Package">
      <main style={{ position: 'relative', height: '100vh', overflow: 'hidden' }}>
        {isLoading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'white',
            zIndex: 10
          }}>
            <p>loading...</p>
          </div>
        )}
        {hasError && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'white',
            zIndex: 10
          }}>
            <p>Loading failed, please try again.</p>
          </div>
        )}
        <iframe
          style={{ height: '100vh', visibility: isLoading ? 'hidden' : 'visible' }}
          title="Embedded Content"
          width="100%"
          height="100vh"
          src="https://docs.zelthy.com/login1/docs/documentation/introduction/"
          frameBorder="0"
          allowFullScreen
          onLoad={handleIframeLoad}
          onError={handleIframeError}
        ></iframe>
      </main>
    </Layout>
  );
}

