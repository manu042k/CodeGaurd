import NextAuth from "next-auth";
import { NextAuthOptions, DefaultSession } from "next-auth";
import GitHubProvider from "next-auth/providers/github";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    username?: string;
    backendUserId?: string;
    backendToken?: string;
    user: {
      id?: string;
    } & DefaultSession["user"];
  }

  interface JWT {
    accessToken?: string;
    username?: string;
    githubId?: string;
    email?: string;
    name?: string;
    avatar_url?: string;
    backendUserId?: string;
    backendToken?: string;
  }
}

const authOptions: NextAuthOptions = {
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: "read:user user:email repo",
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // Persist the OAuth access_token and or the user id to the token right after signin
      if (account) {
        token.accessToken = account.access_token;
        token.githubId = (profile as any)?.id?.toString();
        token.username = (profile as any)?.login;
        token.email = (profile as any)?.email;
        token.name = (profile as any)?.name;
        token.avatar_url = (profile as any)?.avatar_url;

        // Sync user with backend API
        try {
          const response = await fetch(
            `${
              process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            }/api/auth/sync-user`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                github_id: token.githubId,
                username: token.username,
                email: token.email,
                full_name: token.name,
                avatar_url: token.avatar_url,
                github_token: token.accessToken,
              }),
            }
          );

          if (response.ok) {
            const backendUser = await response.json();
            token.backendUserId = backendUser.id;
            token.backendToken = backendUser.jwt_token;
          }
        } catch (error) {
          console.error("Failed to sync user with backend:", error);
        }
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user id from a provider.
      if (session.user) {
        session.accessToken = token.accessToken as string;
        session.user.id = token.githubId as string;
        session.username = token.username as string;
        session.backendUserId = token.backendUserId as string;
        session.backendToken = token.backendToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },
  session: {
    strategy: "jwt",
  },
  debug: process.env.NODE_ENV === "development",
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST, authOptions };
